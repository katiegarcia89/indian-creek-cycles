/* dispatch.js - Logic for the Unlock/Return Interface */
function loadReservation(event) {
    event.preventDefault();
    const resId = document.getElementById('res-id-input').value;
    if (resId) {
        window.location.href = `?search_id=${resId}`;
    }
}

function handleDockAction(status, resId, unlockUrl, returnUrl) {
    const btn = document.getElementById('action-btn');
    
    if (status === 'completed') return;

    if (status !== 'active') {
        // Handle Unlock logic
        btn.disabled = true;
        btn.innerText = "Connecting...";
        setTimeout(() => { 
            window.location.href = unlockUrl; 
        }, 800);
    } else {
        // Handle Return logic
        if(confirm(`Confirm bike return?`)) {
            btn.disabled = true;
            btn.innerText = "Finalizing...";
            setTimeout(() => { 
                window.location.href = returnUrl; 
            }, 800);
        }
    }
}