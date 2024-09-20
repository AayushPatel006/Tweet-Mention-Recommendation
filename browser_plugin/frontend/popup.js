var response = null;

var useLocation = true;

// Load the saved toggle state when the popup opens
chrome.storage.local.get(['useLocation'], function (result) {
  if (result.useLocation !== undefined) {
    useLocation = result.useLocation;
    document.getElementById('location-toggle').checked = useLocation;
    updateLocationWarning();
    updateGeoInfoVisibility();
  }
});

document.getElementById('location-toggle').addEventListener('change', (event) => {
  useLocation = event.target.checked;
  console.log('Location use toggled:', useLocation);

  // Save the toggle state
  chrome.storage.local.set({ useLocation: useLocation }, function () {
    console.log('Toggle state saved');
  });

  updateLocationWarning();
  updateGeoInfoVisibility();

  // Re-fetch data with or without location
  chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    chrome.tabs.sendMessage(tabs[0].id, { action: "scrape" }, function (response) {
      if (response && response.data) {
        getLocationCoordinates(response.data);
      }
    });
  });
});

function updateLocationWarning() {
  const warningElement = document.getElementById('locationWarning');
  if (useLocation) {
    warningElement.textContent = "Note: Your location coordinates are being used to provide more accurate suggestions.";
  } else {
    warningElement.textContent = "Note: Location services are disabled. Enable them for more accurate suggestions.";
  }
}

function updateGeoInfoVisibility() {
  const geoInfoDiv = document.getElementById('geoInfo');
  if (useLocation) {
    geoInfoDiv.style.display = 'block';
  } else {
    geoInfoDiv.style.display = 'none';
    geoInfoDiv.textContent = 'Location not used.';
  }
}

function getLocationCoordinates(tweet, request_type = "suggest", tweetLink = null) {
  if (useLocation && navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;
        updateGeoInfo(`Latitude: ${latitude}, Longitude: ${longitude}`);
        sendApiRequest(tweet, String(latitude), String(longitude), request_type, tweetLink);
      },
      (error) => {
        updateGeoInfo(`Error getting location: ${error.message}`);
        sendApiRequest(tweet, null, null, request_type, tweetLink);
      }
    );
  } else {
    updateGeoInfo('Location not used.');
    sendApiRequest(tweet, null, null, request_type, tweetLink);
  }
}

function sendApiRequest(data, latitude, longitude, request_type = "suggest", tweetLink = null) {
  const apiUrl = 'http://localhost:8000/test';

  fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      data: {
        tweet: data,
        coordinates: latitude && longitude ? {
          latitude: latitude,
          longitude: longitude
        } : {
          latitude: "",
          longitude: ""
        },
        request_type: request_type,
        tweet_link: tweetLink ? tweetLink : "null"
      }
    }),
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      console.log('API response:', JSON.stringify(data));
      updateResult(data['message']);
      updateSuggestions(data['suggestion']);
    })
    .catch(error => {
      updateResult('Error sending API request:', JSON.stringify(error));
    });
}

function updateGeoInfo(message) {
  const outputDiv = document.getElementById('geoInfo');
  outputDiv.textContent = message;
}

function updateResult(message) {
  const outputDiv = document.getElementById('result');
  outputDiv.textContent = message;
}

function updateSuggestions(message) {
  const outputDiv = document.getElementById('suggestions');
  outputDiv.textContent = message;
}

function updateOutput(data) {
  document.getElementById('output').textContent = data || 'No tweet found';
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'updatePopup') {
    if (request.request_type === "post") {
      const tweetContent = document.getElementById('output').textContent;
      getLocationCoordinates(tweetContent, request.request_type, request.tweetLink);
    } else {
      getLocationCoordinates(request.data);
    }
    updateOutput(request.data);
  }
});

// Call this function when the popup is opened
document.addEventListener('DOMContentLoaded', function() {
  updateLocationWarning();
  
  // Add event listener for copy button
  const copyButton = document.getElementById('copy-button');
  copyButton.addEventListener('click', copyRecommendation);
});

// Add this function to handle copying the recommendation
function copyRecommendation() {
  const resultDiv = document.getElementById('result');
  const text = resultDiv.textContent;
  
  // Extract the mention from the text (assuming it's always at the end after a colon)
  const mention = text.split(':').pop().trim();
  
  navigator.clipboard.writeText(mention).then(() => {
    console.log('Recommendation copied to clipboard');
    // Optionally, provide visual feedback that the copy was successful
    const copyButton = document.getElementById('copy-button');
    copyButton.textContent = 'Copied!';
    setTimeout(() => {
      copyButton.textContent = 'Copy';
    }, 2000);
  }).catch(err => {
    console.error('Failed to copy: ', err);
  });
}
