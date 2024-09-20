let popupWindowId = null;
let scrapedData = null;


function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}


chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'openPopup') {
    console.log('Opening popup');
    console.log('Data:', request.data);
    scrapedData = request.data;
    createPopup();
  } else if (request.action === 'scrapedData') {
    scrapedData = request.data;
    if (popupWindowId !== null) {
      chrome.runtime.sendMessage({ action: 'updatePopup', data: scrapedData });
    }
    console.log('Scraped data:', scrapedData);
  }
});

function createPopup() {
  // Close the existing popup if it's open
  if (popupWindowId !== null) {
    chrome.windows.remove(popupWindowId, () => {
      openNewPopup();
    });
  } else {
    openNewPopup();
  }
}

function openNewPopup() {
  chrome.windows.create({
    url: chrome.runtime.getURL("popup.html"),
    type: "popup",
    width: 408,
    height: 520
  }, (popupWindow) => {
    popupWindowId = popupWindow.id;
    if (scrapedData) {
      sleep(1000).then(() => {
        chrome.runtime.sendMessage({ action: 'updatePopup', data: scrapedData });
      });
    }

    // Listen for window close event
    chrome.windows.onRemoved.addListener(function windowClosedListener(windowId) {
      if (windowId === popupWindowId) {
        popupWindowId = null;
        chrome.windows.onRemoved.removeListener(windowClosedListener);
      }
    });
  });
}


chrome.action.onClicked.addListener((tab) => {
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ['content.js']
  }, () => {
    chrome.tabs.sendMessage(tab.id, { action: 'scrape' }, (response) => {
      if (response && response.data) {
        console.log('Scraped data:', response.data);
      } else {
        console.log('No data found or element not present.');
      }
    });
  });
});
