function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

let typingTimer;                // Timer identifier
const typingInterval = 3000;


function scrapeData() {
  var spanElement = document.querySelector(`div[class="public-DraftStyleDefault-block public-DraftStyleDefault-ltr"]`)

  if (spanElement && spanElement.textContent != "") {

    var textContent = spanElement.textContent;
    console.log("Scraped content:", textContent);
    return textContent;
  } else {
    console.log("Element not found");
    return null;
  }
}

function getTweetDetails() {
  let usernameElement = document.querySelector(`span[class="css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3"]`);
  let tweetLinkElement = document.querySelector(`a[role="link"][href^="/"][href*="/status/"]`);

  let username = usernameElement ? usernameElement.textContent : null;
  let tweetLink = tweetLinkElement ? tweetLinkElement.href : null;

  console.log("Scraped username:", username);
  console.log("Scraped tweet link:", tweetLink);

  return { username, tweetLink };
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'scrape') {
    const data = scrapeData();
    sendResponse({ data: data });
  }
});

function doneTyping() {
  let data = scrapeData();
  data = null ? data = "" : data = data;
  console.log("Data scraped in donetyping:", data);
  chrome.runtime.sendMessage({ action: 'scrapedData', data: data });
  chrome.runtime.sendMessage({ action: 'openPopup', data: data, request_type: "post" });
}

sleep(10000).then(() => {

  var spanElement = document.querySelector(`div[class="public-DraftStyleDefault-block public-DraftStyleDefault-ltr"]`);
  if (spanElement) {

    document.querySelector(`div[class="public-DraftStyleDefault-block public-DraftStyleDefault-ltr"]`).addEventListener('contentChanged', () => {
      console.log('Content has changed');
      clearTimeout(typingTimer);
      typingTimer = setTimeout(doneTyping, typingInterval);
    });

    document.addEventListener('click', function (event) {
      var tweetButton = event.target.closest('button[data-testid="tweetButtonInline"]');
      if (tweetButton) {
        console.log("Post Button clicked");
        // Wait for the tweet to be posted and the page to update
        setTimeout(() => {
          let { username, tweetLink } = getTweetDetails();
          if (tweetLink) {
            chrome.runtime.sendMessage({ 
              action: 'updatePopup', 
              request_type: "post",
              tweetLink: tweetLink
            });
          } else {
            console.log("Failed to get tweet link");
          }
        }, 2000); // Adjust this delay if needed
      }
    });
    console.log("Listener added to the text area")
  }
  else {
    console.log("Element not found in listener");
  }

  let lastContent = spanElement.textContent;

  setInterval(checkForChanges, 500);

  function checkForChanges() {
    const currentContent = document.querySelector(`div[class="public-DraftStyleDefault-block public-DraftStyleDefault-ltr"]`).textContent;
    if (currentContent !== lastContent) {
      lastContent = currentContent;

      const event = new Event('contentChanged');
      document.querySelector(`div[class="public-DraftStyleDefault-block public-DraftStyleDefault-ltr"]`).dispatchEvent(event);
    }
  }
});
