/**
 * API client for Pokemon Card Arbitrage Tool
 */

const API = {
  /**
   * Get price data and arbitrage opportunities for a card
   * @param {Object} cardData - Card data object
   * @returns {Promise} - Promise resolving to arbitrage data
   */
  getCardPrices: async (cardData) => {
    try {
      const response = await fetch("/api/card_prices", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(cardData),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error fetching card prices:", error);
      throw error;
    }
  },
};

export default API;
