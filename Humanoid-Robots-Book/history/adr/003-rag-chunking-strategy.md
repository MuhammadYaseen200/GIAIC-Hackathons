# ADR-003: RAG Chunking Strategy - Token Size and Overlap Configuration

**Status**: Accepted
**Date**: 2025-12-12
**Context**: Feature 001-physical-ai-textbook
**Deciders**: System (Claude Sonnet 4.5), pending human approval

## Context and Problem Statement

User Story 2 (RAG Chatbot) requires ingesting all textbook chapters into Qdrant vector database for semantic retrieval. Qdrant Cloud Free Tier has a **1GB storage limit**. We need to determine:

1. **Chunk size**: How many tokens per chunk?
2. **Overlap**: How many tokens overlap between consecutive chunks?
3. **Metadata strategy**: What payload fields to store for filtering?

This decision impacts:
- **Storage usage**: Smaller chunks = more vectors, larger chunks = fewer vectors
- **Retrieval accuracy**: Optimal chunk size balances context and precision
- **Query performance**: More chunks = slower search, metadata filtering improves speed

## Decision Drivers

- **Storage constraint**: Must stay within 1GB limit for 13+ chapters (~250 total chapters max for future)
- **Retrieval accuracy**: Chunks must preserve semantic context for technical concepts
- **Query performance**: <10s response time for chatbot (p95)
- **Cost efficiency**: Maximize content coverage within free tier
- **Future scalability**: Leave headroom for additional chapters beyond hackathon

## Considered Options

### Option A: 512-Token Chunks with 50-Token Overlap

**Configuration**:
- **Chunk size**: 512 tokens (~2048 characters, ~350 words)
- **Overlap**: 50 tokens (~10% overlap to preserve context across boundaries)
- **Vector dimensions**: 1536 (OpenAI text-embedding-3-small)
- **Metadata fields**: chapter_id, module, week_number, chunk_index, heading, token_count

**Storage Calculation**:
- **Average chapter**: 1500 words = ~2000 tokens
- **Chunks per chapter**: 2000 / (512 - 50) ≈ 4.3 chunks → round to 5 chunks
- **13 chapters**: 13 × 5 = 65 chunks
- **Vector size**: 1536 dimensions × 4 bytes (float32) = 6KB per vector
- **Metadata size**: ~500 bytes per chunk (text fields + integers)
- **Total per chunk**: 6KB (vector) + 0.5KB (metadata) + 2KB (original text stored) = 8.5KB
- **Total for 13 chapters**: 65 chunks × 8.5KB = **553KB**
- **Headroom**: 1GB - 553KB = 999.4MB remaining (supports ~12,000 more chunks = **2,400+ future chapters**)

**Pros**:
- ✅ **Well within 1GB limit**: Only 0.05% of storage used for 13 chapters
- ✅ **Proven chunk size**: 512 tokens is standard in RAG literature (balances context and precision)
- ✅ **Good semantic coverage**: Enough context for multi-paragraph technical explanations
- ✅ **Overlap preserves continuity**: 50-token overlap prevents splitting concepts across chunks
- ✅ **Fast retrieval**: 65 chunks searchable in <100ms on Qdrant

**Cons**:
- ❌ **Potential over-chunking**: Some short sections (<512 tokens) create small chunks
- ❌ **Metadata duplication**: Storing original text in payload increases size (mitigable by omitting text, storing only chunk_id)

### Option B: 1024-Token Chunks with 100-Token Overlap

**Configuration**:
- **Chunk size**: 1024 tokens (~4096 characters, ~700 words)
- **Overlap**: 100 tokens (~10% overlap)

**Storage Calculation**:
- **Chunks per chapter**: 2000 / (1024 - 100) ≈ 2.2 chunks → round to 3 chunks
- **13 chapters**: 13 × 3 = 39 chunks
- **Total for 13 chapters**: 39 chunks × 8.5KB = **332KB**
- **Headroom**: 1GB - 332KB = 999.7MB remaining

**Pros**:
- ✅ **Fewer chunks**: Reduces vector count by 40% vs. Option A
- ✅ **Larger context windows**: Better for long explanations (e.g., URDF format specification)

**Cons**:
- ❌ **Reduced precision**: Larger chunks mix multiple concepts, harder to retrieve specific sentences
- ❌ **Worse "Ask about selection" mode**: User-selected text (up to 2000 chars) might span multiple concepts in large chunk
- ❌ **Less standard**: 1024 tokens exceeds typical RAG recommendations (512-768 tokens)

### Option C: 256-Token Chunks with 25-Token Overlap

**Configuration**:
- **Chunk size**: 256 tokens (~1024 characters, ~175 words)
- **Overlap**: 25 tokens

**Storage Calculation**:
- **Chunks per chapter**: 2000 / (256 - 25) ≈ 8.7 chunks → round to 9 chunks
- **13 chapters**: 13 × 9 = 117 chunks
- **Total for 13 chapters**: 117 chunks × 8.5KB = **995KB**

**Pros**:
- ✅ **High precision**: Small chunks focus on single concepts
- ✅ **Better for "Ask about selection"**: Selected text likely within single chunk

**Cons**:
- ❌ **Context fragmentation**: 256 tokens may split complex explanations across too many chunks
- ❌ **More vectors to search**: 117 chunks slower than 65 chunks (still <200ms, acceptable)
- ❌ **Higher storage usage**: Approaches 1GB for just 13 chapters (limits future scalability)

## Decision Outcome

**Chosen option**: **Option A - 512-Token Chunks with 50-Token Overlap**

**Rationale**:
1. **Industry standard**: 512 tokens is proven optimal for technical documentation in RAG systems (balances context and precision).
2. **Storage efficiency**: Only 0.05% of 1GB used for 13 chapters, leaving 99.95% headroom for future content.
3. **Retrieval accuracy**: 512 tokens captures complete explanations (e.g., "How ROS 2 topics work" fits in single chunk with context).
4. **"Ask about selection" compatibility**: User-selected text up to 2000 chars (~500 tokens) typically fits in one 512-token chunk.
5. **Query performance**: 65 chunks searchable in <100ms, well within <10s chatbot response target.

### Consequences

**Positive**:
- 13 chapters ingested with 65 chunks (~553KB storage)
- Qdrant search returns top 5 chunks in <100ms
- Enough context for GPT-4 to generate accurate answers
- Headroom for 2,400+ future chapters (beyond hackathon scope)

**Negative**:
- Short chapters (<1000 words) may create chunks smaller than 512 tokens (acceptable: not a problem for retrieval)
- Must implement chunking logic (acceptable: use LangChain `RecursiveCharacterTextSplitter` with token counter)

### Implementation Notes

**Chunking implementation** (Python with LangChain):
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken

# Initialize tokenizer (OpenAI's tiktoken for accurate token counting)
encoding = tiktoken.encoding_for_model("text-embedding-3-small")

# Configure splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    length_function=lambda text: len(encoding.encode(text)),
    separators=["\n\n", "\n", ". ", " ", ""]  # Prefer paragraph breaks
)

# Chunk a chapter
chunks = text_splitter.split_text(chapter_markdown)

# Generate embeddings and upload to Qdrant
for idx, chunk in enumerate(chunks):
    embedding = openai.embeddings.create(
        input=chunk,
        model="text-embedding-3-small"
    ).data[0].embedding

    qdrant_client.upsert(
        collection_name="textbook_chunks",
        points=[{
            "id": f"{chapter_id}_{idx}",
            "vector": embedding,
            "payload": {
                "chapter_id": chapter_id,
                "module": module_name,
                "week_number": week_num,
                "chunk_index": idx,
                "text": chunk,  # Store for citation
                "heading": current_heading,  # Extracted from markdown
                "token_count": len(encoding.encode(chunk))
            }
        }]
    )
```

**Retrieval implementation**:
```python
async def query_chatbot(question: str, chapter_id: str = None):
    # Embed question
    query_embedding = openai.embeddings.create(
        input=question,
        model="text-embedding-3-small"
    ).data[0].embedding

    # Search Qdrant
    search_filter = {"chapter_id": chapter_id} if chapter_id else None
    results = qdrant_client.search(
        collection_name="textbook_chunks",
        query_vector=query_embedding,
        limit=5,
        score_threshold=0.7,  # Only return relevant chunks
        query_filter=search_filter
    )

    # Extract context
    context = "\n\n".join([r.payload["text"] for r in results])
    citations = [{"chapter_id": r.payload["chapter_id"],
                  "heading": r.payload["heading"],
                  "score": r.score} for r in results]

    # Generate answer with GPT-4
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Answer based on the provided context from a Physical AI textbook."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]
    )

    return {
        "answer": response.choices[0].message.content,
        "citations": citations
    }
```

**Monitoring storage usage**:
```python
# Check Qdrant collection stats
collection_info = qdrant_client.get_collection("textbook_chunks")
storage_mb = collection_info.points_count * 8.5 / 1024  # Estimate 8.5KB per chunk
print(f"Storage used: {storage_mb:.2f} MB / 1024 MB")
```

## Alternative Considered: Dynamic Chunking

Use heading-based chunking (split at ## and ### markdown headings) instead of fixed token size.

**Why rejected**:
- Unpredictable chunk sizes (some headings have 100 words, others 2000 words)
- Large chunks (2000 words) reduce retrieval precision
- Small chunks (100 words) lack context for complex topics
- Fixed 512-token chunking more consistent and testable

## Links

- **Feature spec**: specs/001-physical-ai-textbook/spec.md (FR-007, FR-008, FR-009)
- **Implementation plan**: specs/001-physical-ai-textbook/plan.md (Phase 2.3)
- **Related ADRs**: ADR-001 (Deployment strategy), ADR-002 (Better Auth integration)
- **Reference**: LangChain text splitters: https://python.langchain.com/docs/modules/data_connection/document_transformers/
