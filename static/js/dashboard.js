document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('active-validation-container');
    if (!container) return;

    const reportId = container.getAttribute('data-report-id');
    const ideaTitleElement = document.getElementById('active-idea-title');
    
    // Status pipeline order
    const pipelineSteps = [
        'market_research',
        'competitor_analysis',
        'customer_persona',
        'revenue_model',
        'swot_analysis',
        'scoring',
        'report_generation'
    ];

    // Establish SSE Connection
    const eventSource = new EventSource(`/dashboard/stream-validation/${reportId}`);

    eventSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            
            if (data.status === 'error') {
                console.error(data.message);
                eventSource.close();
                alert(`Error: ${data.message}`);
                window.location.href = '/dashboard/';
                return;
            }

            // Update idea title
            if (data.idea_title) {
                ideaTitleElement.textContent = data.idea_title;
            }

            const currentStatus = data.status;
            console.log('Validation status update:', currentStatus);

            if (currentStatus === 'completed') {
                // Highlight all steps as completed
                pipelineSteps.forEach(step => {
                    const row = document.getElementById(`step-${step}`);
                    if (row) {
                        row.className = 'step-row completed';
                        const icon = row.querySelector('.step-icon');
                        if (icon) icon.innerHTML = '<i class="fa-solid fa-check"></i>';
                    }
                });
                
                eventSource.close();
                
                // Show completed message and redirect
                const titleText = container.querySelector('.active-title span');
                const titleIcon = container.querySelector('.active-title i');
                if (titleText) titleText.textContent = 'Validation Complete! Redirecting...';
                if (titleIcon) titleIcon.className = 'fa-solid fa-circle-check text-success';
                
                setTimeout(() => {
                    window.location.href = `/dashboard/report/${reportId}`;
                }, 1500);
                return;
            }

            if (currentStatus === 'failed') {
                eventSource.close();
                alert(`Validation failed: ${data.error_message || 'Unknown error occurred'}`);
                window.location.href = '/dashboard/';
                return;
            }

            // Update individual step rows based on the pipeline progress
            const currentStepIndex = pipelineSteps.indexOf(currentStatus);
            
            pipelineSteps.forEach((step, index) => {
                const row = document.getElementById(`step-${step}`);
                if (!row) return;

                const icon = row.querySelector('.step-icon');

                if (index < currentStepIndex) {
                    // Step is completed
                    row.className = 'step-row completed';
                    if (icon) icon.innerHTML = '<i class="fa-solid fa-check"></i>';
                } else if (index === currentStepIndex) {
                    // Step is currently active
                    row.className = 'step-row active';
                    if (icon) icon.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
                } else {
                    // Step has not started yet
                    row.className = 'step-row';
                    if (icon) icon.innerHTML = index + 1;
                }
            });

        } catch (err) {
            console.error('Error parsing SSE event:', err);
        }
    };

    eventSource.onerror = function(err) {
        console.error('SSE connection lost or error:', err);
        // Connection drops are handled by browser auto-reconnect, but if it dies permanently:
        // We do not close unless explicitly required, to let the browser retry.
    };
});
