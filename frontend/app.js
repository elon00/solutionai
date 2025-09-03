document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('triage-form');
    const resultDiv = document.getElementById('result');
    const labelSpan = document.getElementById('label');
    const confidenceSpan = document.getElementById('confidence');
    const summarySpan = document.getElementById('summary');
    const loadRecentBtn = document.getElementById('load-recent');
    const recentListDiv = document.getElementById('recent-list');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const apiKey = document.getElementById('api-key').value;
        const ticketText = document.getElementById('ticket-text').value;

        try {
            const response = await fetch('http://localhost:8000/api/v1/triage', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Api-Key': apiKey
                },
                body: JSON.stringify({ ticket_text: ticketText })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            labelSpan.textContent = data.label;
            confidenceSpan.textContent = (data.confidence * 100).toFixed(2) + '%';
            summarySpan.textContent = data.summary;
            resultDiv.classList.remove('hidden');
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });

    loadRecentBtn.addEventListener('click', async () => {
        const apiKey = document.getElementById('api-key').value;
        if (!apiKey) {
            alert('Please enter your API key first');
            return;
        }

        try {
            const response = await fetch('http://localhost:8000/api/v1/recent', {
                headers: {
                    'X-Api-Key': apiKey
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            recentListDiv.innerHTML = '';
            data.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'recent-item';
                itemDiv.innerHTML = `
                    <h4>${item.label} (${(item.confidence * 100).toFixed(2)}%)</h4>
                    <p><strong>Ticket:</strong> ${item.ticket_text}</p>
                    <p><strong>Summary:</strong> ${item.summary}</p>
                    <p><strong>Timestamp:</strong> ${new Date(item.timestamp).toLocaleString()}</p>
                `;
                recentListDiv.appendChild(itemDiv);
            });
        } catch (error) {
            alert('Error loading recent tickets: ' + error.message);
        }
    });
});