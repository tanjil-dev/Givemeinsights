// Upload Excel File
document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    const formData = new FormData(this); // Collect form data

    fetch('/api/upload-excel/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',  // Pass the CSRF token for security
        }
    })
    .then(response => response.json())
    .then(data => {
        const messageDiv = document.getElementById('upload-message');
        if (data.message) {
            messageDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
        } else if (data.error) {
            messageDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        }
    })
    .catch(error => {
        console.error('Error uploading file:', error);
        alert('Error uploading file. Please try again.');
    });
});

// Fetch and Display Uploaded Data
document.getElementById("see-uploaded-data").addEventListener("click", function() {
    fetch('/api/persons/')  // API endpoint for showing the data
        .then(response => response.json())
        .then(data => {
            const table = document.getElementById("person-table");
            const tbody = table.querySelector("tbody");
            tbody.innerHTML = "";  // Clear previous data

            data.forEach(person => {
                const row = document.createElement("tr");
                row.innerHTML = `<td>${person.name}</td><td>${person.address}</td>`;
                tbody.appendChild(row);
            });

            // Show the table
            table.style.display = "table";
        })
        .catch(error => {
            console.error("Error fetching data:", error);
        });
});

// Event listener for deleting all data
document.getElementById("delete-all-data").addEventListener("click", function() {
if (confirm("Are you sure you want to delete all data?")) {
    fetch('/api/persons/', {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',  // Ensure you include CSRF token
        }
    })
    .then(response => {
        if (response.status === 204) {
            alert("All data deleted successfully!");
            // Optionally hide the table after deleting
            document.getElementById("person-table").style.display = "none";
        } else {
            alert("Failed to delete data.");
        }
    })
    .catch(error => {
        console.error("Error deleting data:", error);
    });
}
});

window.addEventListener('load', function() {
        // Select the footer element and hide it
        var footer = document.querySelector('p.text-body-secondary.text-end');
        if (footer) {
            footer.style.display = 'none';
        }
    });