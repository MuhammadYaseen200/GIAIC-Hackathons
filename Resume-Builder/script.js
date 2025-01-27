// TypeScript file for Dynamic Resume Builder
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var _a, _b, _c, _d, _e, _f, _g, _h;
var _this = this;
// Education Section
var educationCount = 0;
function addEducation() {
    educationCount++;
    var educationList = document.getElementById('education-list');
    var educationDiv = document.createElement('div');
    educationDiv.className = 'education-item';
    educationDiv.innerHTML = "\n        <h3>Education ".concat(educationCount, "</h3>\n        <label for=\"degree-").concat(educationCount, "\">Degree:</label>\n        <input type=\"text\" id=\"degree-").concat(educationCount, "\" name=\"degree-").concat(educationCount, "\">\n        <label for=\"institution-").concat(educationCount, "\">Institution:</label>\n        <input type=\"text\" id=\"institution-").concat(educationCount, "\" name=\"institution-").concat(educationCount, "\">\n        <label for=\"start-date-").concat(educationCount, "\">Start Date:</label>\n        <input type=\"date\" id=\"start-date-").concat(educationCount, "\" name=\"start-date-").concat(educationCount, "\" class=\"start-date\">\n        <label for=\"end-date-").concat(educationCount, "\">End Date:</label>\n        <input type=\"date\" id=\"end-date-").concat(educationCount, "\" name=\"end-date-").concat(educationCount, "\" class=\"end-date\">\n    ");
    educationList.appendChild(educationDiv);
}
// Work Section
var workCount = 0;
function addWork() {
    workCount++;
    var workList = document.getElementById('work-list');
    var workDiv = document.createElement('div');
    workDiv.className = 'work-item';
    workDiv.innerHTML = "\n        <h3>Work Experience ".concat(workCount, "</h3>\n        <label for=\"job-title-").concat(workCount, "\">Job Title:</label>\n        <input type=\"text\" id=\"job-title-").concat(workCount, "\" name=\"job-title-").concat(workCount, "\">\n        <label for=\"firm-").concat(workCount, "\">Firm:</label>\n        <input type=\"text\" id=\"firm-").concat(workCount, "\" name=\"firm-").concat(workCount, "\">\n        <label for=\"start-date-").concat(workCount, "\">Start Date:</label>\n        <input type=\"date\" id=\"start-date-").concat(workCount, "\" name=\"start-date-").concat(workCount, "\" class=\"start-date\">\n        <label for=\"end-date-").concat(workCount, "\">End Date:</label>\n        <input type=\"date\" id=\"end-date-").concat(workCount, "\" name=\"end-date-").concat(workCount, "\" class=\"end-date\">\n    ");
    workList.appendChild(workDiv);
}
// Skills Section
var skillCount = 0;
function addSkill() {
    skillCount++;
    var skillsList = document.getElementById('skills-list');
    var skillDiv = document.createElement('div');
    skillDiv.className = 'skill-item';
    skillDiv.innerHTML = "\n        <h3>Skill ".concat(skillCount, "</h3>\n        <label for=\"skill-").concat(skillCount, "\">Skill Name:</label>\n        <input type=\"text\" id=\"skill-").concat(skillCount, "\" name=\"skill-").concat(skillCount, "\" placeholder=\"Enter your skill\">\n        <label for=\"proficiency-").concat(skillCount, "\">Proficiency Level (1-10):</label>\n        <input type=\"number\" id=\"proficiency-").concat(skillCount, "\" name=\"proficiency-").concat(skillCount, "\" min=\"1\" max=\"10\" placeholder=\"Enter proficiency level\" class=\"skill\">\n    ");
    skillsList.appendChild(skillDiv);
}
//Edit Button
var editButton = document.getElementById('edit-btn');
//download button
var downloadButton = document.getElementById('download-btn');
// Social Media Section
var socialMediaCount = 0;
function addSocialMedia() {
    socialMediaCount++;
    var socialMediaList = document.getElementById('social-media-list');
    var socialMediaDiv = document.createElement('div');
    socialMediaDiv.className = 'social-media-item';
    socialMediaDiv.innerHTML = "\n    <h3>Social Media ".concat(socialMediaCount, "</h3>\n    <label for=\"platform-").concat(socialMediaCount, "\">Platform:</label>\n    <input type=\"text\" id=\"platform-").concat(socialMediaCount, "\" name=\"platform-").concat(socialMediaCount, "\">\n    <label for=\"link-").concat(socialMediaCount, "\">Link:</label>\n    <input type=\"text\" id=\"link-").concat(socialMediaCount, "\" name=\"link-").concat(socialMediaCount, "\">\n    ");
    socialMediaList.appendChild(socialMediaDiv);
}
// Reference the download button
// Event Listeners
(_a = document.getElementById('add-education')) === null || _a === void 0 ? void 0 : _a.addEventListener('click', addEducation);
(_b = document.getElementById('add-work')) === null || _b === void 0 ? void 0 : _b.addEventListener('click', addWork);
(_c = document.getElementById('add-skill')) === null || _c === void 0 ? void 0 : _c.addEventListener('click', addSkill);
(_d = document.getElementById('add-social-media')) === null || _d === void 0 ? void 0 : _d.addEventListener('click', addSocialMedia);
// Form Submission Handling
var form = document.getElementById('resume-builder-form');
form.addEventListener('submit', function (event) {
    var _a;
    event.preventDefault(); // Prevent form from actually submitting
    var outputDiv = document.getElementById('output');
    outputDiv.style.display = 'block'; // Show output section
    // Clear previous output
    document.getElementById('output-education').innerHTML = '';
    document.getElementById('output-work').innerHTML = '';
    document.getElementById('output-skills').innerHTML = '';
    document.getElementById('output-social-media').innerHTML = '';
    document.getElementById('output-summary').innerHTML = '';
    // Displaying general information
    var jobTitle = document.getElementById('job-title').value;
    var name = document.getElementById('name').value;
    var contactNumber = document.getElementById('number').value;
    var email = document.getElementById('email').value;
    var address = document.getElementById('address').value;
    var summary = document.getElementById('summary-text').value;
    // Set the header
    document.getElementById('output-job-title').textContent = jobTitle;
    document.getElementById('output-name').textContent = name;
    document.getElementById('output-contact').innerHTML = "Contact: ".concat(contactNumber, ", <div class=\"email\"> Email: ").concat(email, "</div>");
    document.getElementById('output-address').innerHTML = "Address: ".concat(address);
    document.getElementById('output-summary').textContent = summary;
    // Education
    var educationItems = document.querySelectorAll('.education-item');
    educationItems.forEach(function (item) {
        var degree = item.querySelector("input[name^=\"degree\"]").value;
        var institution = item.querySelector("input[name^=\"institution\"]").value;
        var startDate = item.querySelector("input[name^=\"start-date\"]").value;
        var endDate = item.querySelector("input[name^=\"end-date\"]").value;
        if (degree || institution) {
            var listItem = document.createElement('li');
            listItem.innerHTML = "<strong>Degree:</strong> ".concat(degree, ",<strong> Institution:</strong> ").concat(institution, " <br>\n             <div class=\"italic\">Start Date:</div> ").concat(startDate, " - <div class=\"italic\">End Date:</div> ").concat(endDate, "\n            ");
            document.getElementById('output-education').appendChild(listItem);
        }
    });
    // Work Experience
    var workItems = document.querySelectorAll('.work-item');
    workItems.forEach(function (item) {
        var job = item.querySelector("input[name^=\"job-title\"]").value;
        var firm = item.querySelector("input[name^=\"firm\"]").value;
        var startDate = item.querySelector("input[name^=\"start-date\"]").value;
        var endDate = item.querySelector("input[name^=\"end-date\"]").value;
        if (job || firm) {
            var listItem = document.createElement('li');
            listItem.innerHTML = "<strong>Job:</strong> ".concat(job, ",<strong> Firm:</strong> ").concat(firm, " <br>\n             <div class=\"italic\">Start Date:</div> ").concat(startDate, " - <div class=\"italic\">End Date:</div> ").concat(endDate);
            document.getElementById('output-work').appendChild(listItem);
        }
    });
    // Skills
    var skillItems = document.querySelectorAll('.skill-item');
    skillItems.forEach(function (item) {
        var skillName = item.querySelector("input[name^=\"skill\"]").value;
        var proficiency = item.querySelector("input[name^=\"proficiency\"]").value;
        if (skillName || proficiency) {
            var listItem = document.createElement('li');
            listItem.innerHTML = "<strong>Skill:</strong> ".concat(skillName, ", <br><strong>Proficiency:</strong> ").concat(proficiency, "/10");
            document.getElementById('output-skills').appendChild(listItem);
        }
    });
    // Social Media
    var socialMediaItems = document.querySelectorAll('.social-media-item');
    socialMediaItems.forEach(function (item) {
        var platform = item.querySelector("input[name^=\"platform\"]").value;
        var link = item.querySelector("input[name^=\"link\"]").value;
        if (platform || link) {
            var listItem = document.createElement('li');
            listItem.innerHTML = "<strong>Platform:</strong><a href = ".concat(link, "> ").concat(platform, "</a>");
            document.getElementById('output-social-media').appendChild(listItem);
        }
    });
    // Image Preview
    var profilePictureInput = document.getElementById('profile-picture');
    var outputImage = document.getElementById('output-picture');
    if ((_a = profilePictureInput.files) === null || _a === void 0 ? void 0 : _a.length) {
        var reader_1 = new FileReader();
        reader_1.onload = function () {
            outputImage.src = reader_1.result;
            outputImage.style.display = 'block'; // Show the image
        };
        reader_1.readAsDataURL(profilePictureInput.files[0]);
    }
    // Show the Edit and Download buttons
    editButton.style.display = 'block';
    downloadButton.style.display = 'block';
});
// Add event listeners for adding education, skills, work, and social media
(_e = document.getElementById('add-education')) === null || _e === void 0 ? void 0 : _e.addEventListener('click', addEducation);
(_f = document.getElementById('add-work')) === null || _f === void 0 ? void 0 : _f.addEventListener('click', addWork);
(_g = document.getElementById('add-skill')) === null || _g === void 0 ? void 0 : _g.addEventListener('click', addSkill);
(_h = document.getElementById('add-social-media')) === null || _h === void 0 ? void 0 : _h.addEventListener('click', addSocialMedia);
// Add functionality for the Edit button
editButton.addEventListener('click', function () {
    var _a, _b;
    // Hide the output and show the form again
    document.getElementById('output').style.display = 'none';
    form.style.display = 'block';
    // Repopulate the form fields from the previously displayed data
    var jobTitle = document.getElementById('output-job-title').textContent;
    var name = document.getElementById('output-name').textContent;
    var contactInfo = document.getElementById('output-contact').textContent;
    var address = document.getElementById('output-address').textContent;
    var summary = document.getElementById('output-summary').textContent;
    // Fill back form fields
    document.getElementById('job-title').value = jobTitle || '';
    document.getElementById('name').value = name || '';
    var contactArr = contactInfo === null || contactInfo === void 0 ? void 0 : contactInfo.split(', ');
    if (contactArr) {
        document.getElementById('number').value = ((_a = contactArr[0]) === null || _a === void 0 ? void 0 : _a.split(' ')[1]) || '';
        document.getElementById('email').value = ((_b = contactArr[1]) === null || _b === void 0 ? void 0 : _b.split(' ')[1]) || '';
    }
    document.getElementById('address').value = (address === null || address === void 0 ? void 0 : address.split(': ')[1]) || '';
    document.getElementById('summary-text').value = summary || '';
    // Hide the Edit button again
    editButton.style.display = 'none';
});
// Download the resume as PDF when the button is clicked
downloadButton.addEventListener('click', function () {
    var resumeElement = document.getElementById('output'); // The div containing the resume
    // Use html2pdf to convert the resume to PDF
    var options = {
        margin: [0, 0, 0, 0],
        filename: 'resume.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 1, useCORS: true },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }, // Letter size
    };
    html2pdf().from(resumeElement).set(options).save();
});
//Share Button
var shareButton = document.getElementById('shareBtn');
// Function to generate the PDF Blob
function generatePDFBlob() {
    return __awaiter(this, void 0, void 0, function () {
        var element, options;
        return __generator(this, function (_a) {
            element = document.getElementById('resume');
            options = {
                margin: 0,
                filename: '${name}.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2 },
                jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
            };
            return [2 /*return*/, new Promise(function (resolve, reject) {
                    html2pdf()
                        .from(element)
                        .set(options)
                        .output('blob')
                        .then(function (pdfBlob) { return resolve(pdfBlob); })
                        .catch(function (err) { return reject(err); });
                })];
        });
    });
}
//Sharing the pdf
shareButton.addEventListener('click', function () { return __awaiter(_this, void 0, void 0, function () {
    var pdfBlob, file, error_1;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 5, , 6]);
                return [4 /*yield*/, generatePDFBlob()];
            case 1:
                pdfBlob = _a.sent();
                file = new File([pdfBlob], 'resume.pdf', { type: 'application/pdf' });
                if (!(navigator.canShare && navigator.canShare({ files: [file] }))) return [3 /*break*/, 3];
                return [4 /*yield*/, navigator.share({
                        files: [file],
                        title: 'My Resume',
                        text: 'Here is my resume!',
                    })];
            case 2:
                _a.sent();
                console.log('Resume shared successfully!');
                return [3 /*break*/, 4];
            case 3:
                alert('Sharing files is not supported on this browser/device.');
                _a.label = 4;
            case 4: return [3 /*break*/, 6];
            case 5:
                error_1 = _a.sent();
                console.error('Error sharing the resume:', error_1);
                return [3 /*break*/, 6];
            case 6: return [2 /*return*/];
        }
    });
}); });