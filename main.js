document.addEventListener('DOMContentLoaded', () => {
    // --- Element Selectors ---
    const workshopTypeEl = document.getElementById('workshopType');
    const serviceEl = document.getElementById('service');
    const hoursEl = document.getElementById('hours');
    const framingEl = document.getElementById('framing');

    // --- Price Calculation Logic for Workshop Form ---
    function updateWorkshopPrice() {
        if (!workshopTypeEl) return; // Do nothing if the element doesn't exist

        const workshopType = workshopTypeEl.value;
        let price = 15; // Default for '3day'
        if (workshopType === 'advanced') {
            price = 25;
        } else if (workshopType === 'editing') {
            price = 20;
        }
        document.getElementById('workshopPrice').textContent = `Price: $${price}`;
    }

    // --- Price Calculation Logic for Booking Form ---
    function updateBookingPrice() {
        // Do nothing if the required elements don't exist on the page
        if (!serviceEl || !hoursEl || !framingEl) return;

        const service = serviceEl.value;
        const hours = parseInt(hoursEl.value, 10) || 1;
        let pricePerHour = 0;

        if (service === 'photography') {
            pricePerHour = 30;
        } else if (service === 'videography') {
            // The HTML shows a range of $40-$45. We'll use the lower end for the base calculation.
            pricePerHour = 40;
        }

        let total = pricePerHour * hours;

        if (framingEl.checked) {
            total += 5; // Add the extra for framing
        }

        const priceString = `$${total.toFixed(2)}`;
        
        // 1. Update the visible price display for the user
        document.getElementById('bookingPrice').textContent = `Total: ${priceString}`;

        // 2. CRITICAL: Update the hidden input field that gets submitted
        document.getElementById('totalPriceInput').value = priceString;
    }

    // --- Attach Event Listeners ---
    workshopTypeEl?.addEventListener('change', updateWorkshopPrice);
    serviceEl?.addEventListener('change', updateBookingPrice);
    hoursEl?.addEventListener('input', updateBookingPrice);
    framingEl?.addEventListener('change', updateBookingPrice);

    // --- Initialize Prices on Page Load ---
    updateBookingPrice();
    updateWorkshopPrice();
});