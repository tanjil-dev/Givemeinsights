document.getElementById("see-uploaded-data").addEventListener("click", function() {
    fetch('/api/persons/')  // API endpoint from Django
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