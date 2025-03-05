// If you're using jQuery
function loadCardData(cardId) {
  // Clear previous data
  $("#price-comparison").empty();
  $("#arbitrage-container").empty();
  $("#card-details").empty();

  // Show loading indicator
  $("#loading-indicator").show();

  // Fetch new data
  $.getJSON(`/api/card_prices?id=${cardId}`, function (data) {
    // Hide loading indicator
    $("#loading-indicator").hide();

    // Process and display the data
    displayCardDetails(data);
    displayPriceComparison(data);
    displayArbitrageOpportunity(data);
  }).fail(function (error) {
    console.error("Error loading card data:", error);
    $("#loading-indicator").hide();
    $("#error-message")
      .text("Error loading card data. Please try again.")
      .show();
  });
}
