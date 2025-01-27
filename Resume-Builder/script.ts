// TypeScript file for Dynamic Resume Builder

// Education Section
let educationCount: number = 0;
function addEducation(): void {
    educationCount++;
    const educationList = document.getElementById('education-list') as HTMLElement;
    const educationDiv: HTMLDivElement = document.createElement('div');
    educationDiv.className = 'education-item';

    educationDiv.innerHTML = `
        <h3>Education ${educationCount}</h3>
        <label for="degree-${educationCount}">Degree:</label>
        <input type="text" id="degree-${educationCount}" name="degree-${educationCount}">
        <label for="institution-${educationCount}">Institution:</label>
        <input type="text" id="institution-${educationCount}" name="institution-${educationCount}">
        <label for="start-date-${educationCount}">Start Date:</label>
        <input type="date" id="start-date-${educationCount}" name="start-date-${educationCount}" class="start-date">
        <label for="end-date-${educationCount}">End Date:</label>
        <input type="date" id="end-date-${educationCount}" name="end-date-${educationCount}" class="end-date">
    `;
    educationList.appendChild(educationDiv);
}

// Work Section
let workCount: number = 0;
function addWork(): void {
    workCount++;
    const workList = document.getElementById('work-list') as HTMLElement;
    const workDiv: HTMLDivElement = document.createElement('div');
    workDiv.className = 'work-item';

    workDiv.innerHTML = `
        <h3>Work Experience ${workCount}</h3>
        <label for="job-title-${workCount}">Job Title:</label>
        <input type="text" id="job-title-${workCount}" name="job-title-${workCount}">
        <label for="firm-${workCount}">Firm:</label>
        <input type="text" id="firm-${workCount}" name="firm-${workCount}">
        <label for="start-date-${workCount}">Start Date:</label>
        <input type="date" id="start-date-${workCount}" name="start-date-${workCount}" class="start-date">
        <label for="end-date-${workCount}">End Date:</label>
        <input type="date" id="end-date-${workCount}" name="end-date-${workCount}" class="end-date">
    `;
    workList.appendChild(workDiv);
}

// Skills Section
let skillCount: number = 0;
function addSkill(): void {
    skillCount++;
    const skillsList = document.getElementById('skills-list') as HTMLElement;
    const skillDiv: HTMLDivElement = document.createElement('div');
    skillDiv.className = 'skill-item';

    skillDiv.innerHTML = `
        <h3>Skill ${skillCount}</h3>
        <label for="skill-${skillCount}">Skill Name:</label>
        <input type="text" id="skill-${skillCount}" name="skill-${skillCount}" placeholder="Enter your skill">
        <label for="proficiency-${skillCount}">Proficiency Level (1-10):</label>
        <input type="number" id="proficiency-${skillCount}" name="proficiency-${skillCount}" min="1" max="10" placeholder="Enter proficiency level" class="skill">
    `;
    skillsList.appendChild(skillDiv);
}
//Edit Button
const editButton = document.getElementById('edit-btn') as HTMLButtonElement;
//download button
const downloadButton = document.getElementById('download-btn') as HTMLButtonElement;

// Social Media Section
let socialMediaCount: number = 0;
function addSocialMedia(): void {
    socialMediaCount++;
    const socialMediaList = document.getElementById('social-media-list') as HTMLElement;
    const socialMediaDiv: HTMLDivElement = document.createElement('div');
    socialMediaDiv.className = 'social-media-item';
    
    socialMediaDiv.innerHTML = `
    <h3>Social Media ${socialMediaCount}</h3>
    <label for="platform-${socialMediaCount}">Platform:</label>
    <input type="text" id="platform-${socialMediaCount}" name="platform-${socialMediaCount}">
    <label for="link-${socialMediaCount}">Link:</label>
    <input type="text" id="link-${socialMediaCount}" name="link-${socialMediaCount}">
    `;
    socialMediaList.appendChild(socialMediaDiv);
}
// Reference the download button

// Event Listeners
document.getElementById('add-education')?.addEventListener('click', addEducation);
document.getElementById('add-work')?.addEventListener('click', addWork);
document.getElementById('add-skill')?.addEventListener('click', addSkill);
document.getElementById('add-social-media')?.addEventListener('click', addSocialMedia);

// Form Submission Handling
const form = document.getElementById('resume-builder-form') as HTMLFormElement;
form.addEventListener('submit', function (event: Event): void {
    event.preventDefault(); // Prevent form from actually submitting

    const outputDiv = document.getElementById('output') as HTMLElement;
    outputDiv.style.display = 'block'; // Show output section

    // Clear previous output
    document.getElementById('output-education')!.innerHTML = '';
    document.getElementById('output-work')!.innerHTML = '';
    document.getElementById('output-skills')!.innerHTML = '';
    document.getElementById('output-social-media')!.innerHTML = '';
    document.getElementById('output-summary')!.innerHTML = '';

    // Displaying general information
    const jobTitle = (document.getElementById('job-title') as HTMLInputElement).value;
    const name = (document.getElementById('name') as HTMLInputElement).value;
    const contactNumber = (document.getElementById('number') as HTMLInputElement).value;
    const email = (document.getElementById('email') as HTMLInputElement).value;
    const address = (document.getElementById('address') as HTMLInputElement).value;
    const summary = (document.getElementById('summary-text') as HTMLTextAreaElement).value;

    // Set the header
    document.getElementById('output-job-title')!.textContent = jobTitle;
    document.getElementById('output-name')!.textContent = name;
    document.getElementById('output-contact')!.innerHTML = `Contact: ${contactNumber}, <div class="email"> Email: ${email}</div>`;
    document.getElementById('output-address')!.innerHTML = `Address: ${address}`;
    document.getElementById('output-summary')!.textContent = summary;

    // Education
    const educationItems = document.querySelectorAll('.education-item');
    educationItems.forEach((item: Element) => {
        const degree = (item.querySelector(`input[name^="degree"]`) as HTMLInputElement).value;
        const institution = (item.querySelector(`input[name^="institution"]`) as HTMLInputElement).value;
        const startDate = (item.querySelector(`input[name^="start-date"]`) as HTMLInputElement).value;
        const endDate = (item.querySelector(`input[name^="end-date"]`) as HTMLInputElement).value;
        if (degree || institution) {
            const listItem = document.createElement('li');
            listItem.innerHTML = `<strong>Degree:</strong> ${degree},<strong> Institution:</strong> ${institution} <br>
             <div class="italic">Start Date:</div> ${startDate} - <div class="italic">End Date:</div> ${endDate}
            `;
            document.getElementById('output-education')!.appendChild(listItem);
        }
    });

    // Work Experience
    const workItems = document.querySelectorAll('.work-item');
    workItems.forEach((item: Element) => {
        const job = (item.querySelector(`input[name^="job-title"]`) as HTMLInputElement).value;
        const firm = (item.querySelector(`input[name^="firm"]`) as HTMLInputElement).value;
        const startDate = (item.querySelector(`input[name^="start-date"]`) as HTMLInputElement).value;
        const endDate = (item.querySelector(`input[name^="end-date"]`) as HTMLInputElement).value;
        if (job || firm) {
            const listItem = document.createElement('li');
            listItem.innerHTML = `<strong>Job:</strong> ${job},<strong> Firm:</strong> ${firm} <br>
             <div class="italic">Start Date:</div> ${startDate} - <div class="italic">End Date:</div> ${endDate}`;
            document.getElementById('output-work')!.appendChild(listItem);
        }
    });

    // Skills
    const skillItems = document.querySelectorAll('.skill-item');
    skillItems.forEach((item: Element) => {
        const skillName = (item.querySelector(`input[name^="skill"]`) as HTMLInputElement).value;
        const proficiency = (item.querySelector(`input[name^="proficiency"]`) as HTMLInputElement).value;
        if (skillName || proficiency) {
            const listItem = document.createElement('li');
            listItem.innerHTML = `<strong>Skill:</strong> ${skillName}, <br><strong>Proficiency:</strong> ${proficiency}/10`;
            document.getElementById('output-skills')!.appendChild(listItem);
        }
    });

    // Social Media
    const socialMediaItems = document.querySelectorAll('.social-media-item');
    socialMediaItems.forEach((item: Element) => {
        const platform = (item.querySelector(`input[name^="platform"]`) as HTMLInputElement).value;
        const link = (item.querySelector(`input[name^="link"]`) as HTMLInputElement).value;
        if (platform || link) {
            const listItem = document.createElement('li');
            listItem.innerHTML = `<strong>Platform:</strong><a href = ${link}> ${platform}</a>`;
            document.getElementById('output-social-media')!.appendChild(listItem);
        }
    });

    // Image Preview
    const profilePictureInput = document.getElementById('profile-picture') as HTMLInputElement;
    const outputImage = document.getElementById('output-picture') as HTMLImageElement;
    if (profilePictureInput.files?.length) {
        const reader = new FileReader();
        reader.onload = () => {
            outputImage.src = reader.result as string;
            outputImage.style.display = 'block'; // Show the image
        };
        reader.readAsDataURL(profilePictureInput.files[0]);
    }
    
    // Show the Edit and Download buttons
    editButton.style.display = 'block';
    downloadButton.style.display = 'block';
});

// Add event listeners for adding education, skills, work, and social media
document.getElementById('add-education')?.addEventListener('click', addEducation);
document.getElementById('add-work')?.addEventListener('click', addWork);
document.getElementById('add-skill')?.addEventListener('click', addSkill);
document.getElementById('add-social-media')?.addEventListener('click', addSocialMedia);

// Add functionality for the Edit button
editButton.addEventListener('click', function (): void {
    // Hide the output and show the form again
    document.getElementById('output')!.style.display = 'none';
    form.style.display = 'block';

    // Repopulate the form fields from the previously displayed data
    const jobTitle = (document.getElementById('output-job-title') as HTMLElement).textContent;
    const name = (document.getElementById('output-name') as HTMLElement).textContent;
    const contactInfo = (document.getElementById('output-contact') as HTMLElement).textContent;
    const address = (document.getElementById('output-address') as HTMLElement).textContent;
    const summary = (document.getElementById('output-summary') as HTMLElement).textContent;

    // Fill back form fields
    (document.getElementById('job-title') as HTMLInputElement).value = jobTitle || '';
    (document.getElementById('name') as HTMLInputElement).value = name || '';
    const contactArr = contactInfo?.split(', ');
    if (contactArr) {
        (document.getElementById('number') as HTMLInputElement).value = contactArr[0]?.split(' ')[1] || '';
        (document.getElementById('email') as HTMLInputElement).value = contactArr[1]?.split(' ')[1] || '';
    }
    (document.getElementById('address') as HTMLInputElement).value = address?.split(': ')[1] || '';
    (document.getElementById('summary-text') as HTMLTextAreaElement).value = summary || '';

    // Hide the Edit button again
    editButton.style.display = 'none';
});



// Download the resume as PDF when the button is clicked
downloadButton.addEventListener('click', function (): void {
    const resumeElement = document.getElementById('output')!; // The div containing the resume

    // Use html2pdf to convert the resume to PDF
    const options = {
        margin: [0, 0, 0, 0], // Remove margins
  filename: 'resume.pdf',
  image: { type: 'jpeg', quality: 0.98 },
  html2canvas: { scale: 1, useCORS: true }, // Scale content to fit
  jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }, // Letter size
    };

    html2pdf().from(resumeElement).set(options).save();
});
//Share Button

const shareButton = document.getElementById('shareBtn')!;

// Function to generate the PDF Blob
async function generatePDFBlob() {
  const element = document.getElementById('resume'); // Your resume container

  const options = {
    margin:       0,
    filename:     'resume.pdf',
    image:        { type: 'jpeg', quality: 0.98 },
    html2canvas:  { scale: 2 },
    jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
  };

  return new Promise((resolve, reject) => {
    html2pdf()
      .from(element)
      .set(options)
      .output('blob')
      .then((pdfBlob) => resolve(pdfBlob))
      .catch((err) => reject(err));
  });
}
//Sharing the pdf
shareButton.addEventListener('click', async () => {
    try {
      const pdfBlob = await generatePDFBlob(); // Get the generated PDF blob
      const file = new File([pdfBlob], 'resume.pdf', { type: 'application/pdf' });
  
      // Check if the Web Share API is available
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({
          files: [file],
          title: 'My Resume',
          text: 'Here is my resume!',
        });
        console.log('Resume shared successfully!');
      } else {
        alert('Sharing files is not supported on this browser/device.');
      }
    } catch (error) {
      console.error('Error sharing the resume:', error);
    }
  });
  