// TypeScript file for Dynamic Resume Builder with Edit Functionality

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
        <input type="date" id="start-date-${educationCount}" name="start-date-${educationCount}">
        <label for="end-date-${educationCount}">End Date:</label>
        <input type="date" id="end-date-${educationCount}" name="end-date-${educationCount}">
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
        <input type="date" id="start-date-${workCount}" name="start-date-${workCount}">
        <label for="end-date-${workCount}">End Date:</label>
        <input type="date" id="end-date-${workCount}" name="end-date-${workCount}">
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
        <input type="number" id="proficiency-${skillCount}" name="proficiency-${skillCount}" min="1" max="10" placeholder="Enter proficiency level">
    `;
    skillsList.appendChild(skillDiv);
}

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

// Form Submission Handling with Edit Functionality
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
    document.getElementById('output-contact')!.textContent = `Contact: ${contactNumber}, Email: ${email}`;
    document.getElementById('output-address')!.textContent = `Address: ${address}`;
    document.getElementById('output-summary')!.textContent = summary;

    // Education
    const educationItems = document.querySelectorAll('.education-item');
    educationItems.forEach((item: Element) => {
        const degree = (item.querySelector(`input[name^="degree"]`) as HTMLInputElement).value;
        const institution = (item.querySelector(`input[name^="institution"]`) as HTMLInputElement).value;
        if (degree || institution) {
            const listItem = document.createElement('li');
            listItem.textContent = `Degree: ${degree}, Institution: ${institution}`;
            document.getElementById('output-education')!.appendChild(listItem);
        }
    });

    // Work Experience
    const workItems = document.querySelectorAll('.work-item');
    workItems.forEach((item: Element) => {
        const job = (item.querySelector(`input[name^="job-title"]`) as HTMLInputElement).value;
        const firm = (item.querySelector(`input[name^="firm"]`) as HTMLInputElement).value;
        if (job || firm) {
            const listItem = document.createElement('li');
            listItem.textContent = `Job Title: ${job}, Firm: ${firm}`;
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
            listItem.textContent = `Skill: ${skillName}, Proficiency: ${proficiency}/10`;
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
            listItem.textContent = `Platform: ${platform}, Link: ${link}`;
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
});

// Edit Functionality
const editBtn = document.createElement('button');
editBtn.textContent = "Edit Resume";
editBtn.addEventListener('click', () => {
    const outputDiv = document.getElementById('output') as HTMLElement;
    outputDiv.style.display = 'none'; // Hide the output
    document.getElementById('resume-builder-form')!.scrollIntoView(); // Scroll back to form for editing
});

document.getElementById('output')!.appendChild(editBtn);
