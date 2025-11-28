document.addEventListener('DOMContentLoaded', () => {
    const adminPanelBtn = document.getElementById('admin-panel-btn');
    const closeAdminPanelBtn = document.getElementById('close-admin-panel');
    const adminPanel = document.getElementById('admin-panel');
    const systemHealth = document.getElementById('system-health');
    const systemLogs = document.getElementById('system-logs');

    const uploadBtn = document.getElementById('upload-btn');
    const planUpload = document.getElementById('plan-upload');

    adminPanelBtn.addEventListener('click', () => {
        adminPanel.style.display = 'block';
        fetchSystemHealth();
        fetchSystemLogs();
    });

    closeAdminPanelBtn.addEventListener('click', () => {
        adminPanel.style.display = 'none';
    });

    uploadBtn.addEventListener('click', () => {
        planUpload.click();
    });

    planUpload.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            uploadPlan(file);
        }
    });

    function fetchSystemHealth() {
        fetch('/api/v1/system/health')
            .then(response => response.json())
            .then(data => {
                systemHealth.innerHTML = `
                    <p>CPU Usage: ${data.data.cpu_usage}</p>
                    <p>Memory Usage: ${data.data.memory_usage}</p>
                    <p>Orchestrator Status: ${data.data.orchestrator_status}</p>
                    <p>Last Analysis Time: ${data.data.last_analysis_time}</p>
                `;
            });
    }

    function fetchSystemLogs() {
        fetch('/api/v1/system/logs')
            .then(response => response.json())
            .then(data => {
                systemLogs.innerHTML = data.data.map(log => `<p>${log}</p>`).join('');
            });
    }

    function uploadPlan(file) {
        const formData = new FormData();
        formData.append('file', file);

        fetch('/api/v1/plans/upload', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            showNotification(data.message);
        })
        .catch(error => {
            showNotification('Error uploading file.');
            console.error('Error:', error);
        });
    }
});
