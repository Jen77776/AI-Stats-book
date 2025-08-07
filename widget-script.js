// widget-script.js
const widget = document.querySelector('.dv-challenge-widget');
const answerForm = widget.querySelector('#answer-form');
const studentAnswerTextarea = widget.querySelector('#student-answer');
const studentIdInput = widget.querySelector('#student-id');
const loader = widget.querySelector('.loader');
const feedbackContainer = widget.querySelector('#feedback-container');
const feedbackResult = widget.querySelector('#feedback-result');
const ratingContainer = widget.querySelector('#rating-container');
const ratingForm = widget.querySelector('#rating-form');
const ratingThanks = widget.querySelector('#rating-thanks');
const promptId = widget.dataset.promptId;

let currentResponseId = null; 

answerForm.addEventListener('submit', function(event) {
    event.preventDefault();
    const studentAnswer = studentAnswerTextarea.value;
    const studentId = studentIdInput.value;
    if (!studentAnswer.trim()) return;

    loader.style.display = 'block';
    feedbackContainer.style.display = 'none';
    ratingContainer.style.display = 'none';
    ratingForm.style.display = 'block';
    ratingThanks.style.display = 'none';

    // 用于本地测试:
    //const apiUrl = 'http://127.0.0.1:5001/api/evaluate';
    // 用于线上部署:
     const apiUrl = 'https://ai-stats-book.onrender.com/api/evaluate';

    fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            answer: studentAnswer,
            student_id: studentId,
            prompt_id: promptId // <-- 将prompt_id发送给后端
        }),
    })
    .then(response => {
        if (!response.ok) { throw new Error('Network response was not ok'); }
        return response.json();
    })
    .then(data => {
        loader.style.display = 'none';
        feedbackResult.innerText = data.feedback;
        feedbackContainer.style.display = 'block';
        if (data.response_id) {
            currentResponseId = data.response_id;
            ratingContainer.style.display = 'block';
        }
    })
    .catch(error => {
        loader.style.display = 'none';
        console.error('Fetch Error:', error);
        feedbackResult.innerText = 'A connection or processing error occurred.';
        feedbackContainer.style.display = 'block';
    });
});

ratingForm.addEventListener('submit', function(event) {
    event.preventDefault();
    const selectedRating = ratingForm.querySelector('input[name="rating"]:checked');
    const comment = widget.querySelector('#rating-comment').value;

    if (!selectedRating) {
        alert("Please select a 1-5 rating.");
        return;
    }

    const ratingData = {
        response_id: currentResponseId,
        rating: parseInt(selectedRating.value, 10),
        comment: comment
    };

    // 用于本地测试:
    //const ratingApiUrl = 'http://127.0.0.1:5001/api/rate-feedback';
    // 用于线上部署:
   const ratingApiUrl = 'https://ai-stats-book.onrender.com/api/rate-feedback';

    fetch(ratingApiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ratingData),
    })
    .then(response => {
        if (response.ok) {
            ratingForm.style.display = 'none';
            ratingThanks.style.display = 'block';
        } else {
            alert("There was an issue submitting your rating.");
        }
    })
    .catch(error => console.error('Rating submission error:', error));
});