// Fetch the CSV file
fetch('static/TopSongs.csv')
    .then(response => response.text())
    .then(data => {
        const musicData = data.split('\n').map(line => line.trim());
        const datalist = document.getElementById('music-suggestions');
        
        // Populate the datalist with music suggestions
        musicData.forEach(music => {
            const option = document.createElement('option');
            option.value = music;
            datalist.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Error:', error);
    });