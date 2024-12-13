// Utility Functions
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.container').firstChild);
}

// Scoring Functions
function validateScore(score) {
    return score >= 1 && score <= 10;
}

function submitScore(pairingId) {
    const scoreInputs = document.querySelectorAll(`#scoring-form-${pairingId} .score-input`);
    const scores = {};
    let isValid = true;

    scoreInputs.forEach(input => {
        const value = parseFloat(input.value);
        if (!validateScore(value)) {
            isValid = false;
            input.classList.add('is-invalid');
        } else {
            input.classList.remove('is-invalid');
            scores[input.name] = value;
        }
    });

    if (!isValid) {
        showAlert('Please enter valid scores (1-10)', 'danger');
        return;
    }

    fetch(`/judge/score/${pairingId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(scores)
    })
    .then(response => response.json())
    .then(data => {
        showAlert('Scores submitted successfully');
        document.querySelector(`#scoring-form-${pairingId}`).reset();
    })
    .catch(error => {
        showAlert('Error submitting scores', 'danger');
    });
}

// Admin Functions
function createCompetition(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    fetch('/admin/competitions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(Object.fromEntries(formData))
    })
    .then(response => response.json())
    .then(data => {
        showAlert('Competition created successfully');
        form.reset();
        location.reload();
    })
    .catch(error => {
        showAlert('Error creating competition', 'danger');
    });
}

function addDancer(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    fetch('/admin/dancers', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(Object.fromEntries(formData))
    })
    .then(response => response.json())
    .then(data => {
        showAlert('Dancer added successfully');
        form.reset();
        location.reload();
    })
    .catch(error => {
        showAlert('Error adding dancer', 'danger');
    });
}

// Results Functions
function loadResults(competitionId) {
    fetch(`/results/${competitionId}`)
        .then(response => response.json())
        .then(data => {
            const resultsContainer = document.getElementById('results-container');
            resultsContainer.innerHTML = '';
            
            data.forEach(round => {
                const roundElement = document.createElement('div');
                roundElement.className = 'mb-4';
                roundElement.innerHTML = `
                    <h3>${round.round} Round</h3>
                    <table class="table results-table">
                        <thead>
                            <tr>
                                <th>Leader</th>
                                <th>Follower</th>
                                <th>Score</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${round.results.map(result => `
                                <tr>
                                    <td>${result.leader}</td>
                                    <td>${result.follower}</td>
                                    <td>${result.score.toFixed(2)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
                resultsContainer.appendChild(roundElement);
            });
        })
        .catch(error => {
            showAlert('Error loading results', 'danger');
        });
}
