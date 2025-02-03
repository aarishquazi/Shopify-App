import React, { useState } from "react";
import "./ShippingCalculator.css"; // Import the custom CSS file

const ShippingCalculator = () => {
  const [address, setAddress] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const calculateShipping = async () => {
    if (!address.trim()) {
      setError("⚠️ Please enter a valid address.");
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/calculate-shipping/?address=${encodeURIComponent(
          address
        )}`,
        {
          method: "POST",
        }
      );
      const data = await response.json();
      if (response.ok) {
        setResult(data);
      } else {
        setError("❌ Failed to fetch shipping options.");
      }
    } catch (err) {
      setError("⚠️ Network error. Please try again.");
    }
    setLoading(false);
  };

  return (
    <div className="container">
      <div className="calculator-card">
        <h2 className="title">🚚 Shipping Calculator</h2>
        <p className="sub-title">
          Enter your address to find the best shipping options.
        </p>

        <div className="address-input">
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="input-field"
            placeholder="Enter your address..."
            autoFocus
          />
          <span className="location-icon">📍</span>
        </div>

        <button
          onClick={calculateShipping}
          className="calculate-button"
          disabled={loading}
        >
          {loading ? "Calculating..." : "🚀 Calculate Shipping"}
        </button>

        {error && <div className="error-message">{error}</div>}

        {result && (
          <div className="results-section">
            <h3 className="results-title">📦 Best Shipping Options:</h3>
            <div className="results-card">
              {["cheapest", "quickest", "balanced"].map((type) => (
                <div key={type} className="result-item">
                  <h4 className="result-title">
                    {type === "cheapest" && "💰 Cheapest"}
                    {type === "quickest" && "⚡ Quickest"}
                    {type === "balanced" && "⚖️ Balanced"}
                  </h4>
                  <p>
                    <strong>Warehouse:</strong> {result[type]?.warehouse}
                  </p>
                  <p>
                    <strong>Method:</strong> {result[type]?.method}
                  </p>
                  <p>
                    <strong>Cost:</strong> ₹
                    {Number(result[type]?.cost).toFixed(2)}
                  </p>
                  <p>
                    <strong>Time:</strong>{" "}
                    {Number(result[type]?.time).toFixed(2)} hrs
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShippingCalculator;
