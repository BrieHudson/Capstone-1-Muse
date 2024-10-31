document.getElementById('search_query').addEventListener('input', function () {
    const query = this.value.trim();

    if (query.length >= 3) {
        // Make an AJAX request to search Spotify
        fetch(`/search_spotify?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                const searchResults = document.getElementById('search_results');
                searchResults.innerHTML = ''; // Clear previous results

                if (data.tracks.length > 0 || data.playlists.length > 0) {
                    searchResults.style.display = 'block';

                    // Display tracks
                    data.tracks.forEach(item => {
                        const resultItem = document.createElement('a');
                        resultItem.classList.add('list-group-item', 'list-group-item-action');
                        resultItem.href = '#';
                        resultItem.textContent = `${item.name} by ${item.artist}`;
                        resultItem.dataset.spotifyId = item.id; // Make sure to use item.id

                        // Add click event listener to each result
                        resultItem.addEventListener('click', function (e) {
                            e.preventDefault();
                            selectSpotifyItem(item); // Call the helper function
                            searchResults.style.display = 'none'; // Hide the search results
                        });

                        searchResults.appendChild(resultItem);
                    });

                    // Display playlists
                    data.playlists.forEach(item => {
                        const resultItem = document.createElement('a');
                        resultItem.classList.add('list-group-item', 'list-group-item-action');
                        resultItem.href = '#';
                        resultItem.textContent = item.name; // Only name for playlists
                        resultItem.dataset.spotifyId = item.id;

                        resultItem.addEventListener('click', function (e) {
                            e.preventDefault();
                            selectSpotifyItem(item); // Call the helper function
                            searchResults.style.display = 'none'; // Hide the search results
                        });

                        searchResults.appendChild(resultItem);
                    });
                } else {
                    searchResults.style.display = 'none'; // No results found
                }
            })
            .catch(error => {
                console.error('Error fetching Spotify data:', error);
                const searchResults = document.getElementById('search_results');
                searchResults.innerHTML = '<p>No results found.</p>'; // Display an error message
                searchResults.style.display = 'block'; // Keep results box visible
            });
    } else {
        document.getElementById('search_results').style.display = 'none';  // Hide results if query is too short
    }
});

function selectSpotifyItem(item) {
    console.log(item);
    const selectedDisplay = document.getElementById('selected_display');
    
     // Access artist directly since it's not an array
     const artistName = item.artist ? item.artist : '';  // Check if artist exists

     // Display song/playlist name with artist if available
     if (artistName) {
         selectedDisplay.innerHTML = `${item.name} by ${artistName}`;
     } else {
         // Display just the song or playlist name if no artist
         selectedDisplay.innerHTML = `${item.name}`;
     }

    // Show the selectedDisplay block
    selectedDisplay.style.display = 'block';

    // Set hidden form fields with selected item's data
    document.getElementById('selected_spotify_id').value = item.id;   // Spotify ID
    document.getElementById('spotify_name').value = item.name;        // Song/Playlist name
    document.getElementById('artist_name').value = artistName;

    // Hide the search results after selecting
    document.getElementById('search_results').style.display = 'none';

    // Clear the search input
    document.getElementById('search_query').value = '';
}

