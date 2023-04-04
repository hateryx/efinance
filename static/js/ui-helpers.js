const button = document.querySelector('button[aria-label="Toggle menu"]');

const show = document.getElementById("show");

button.addEventListener("click", () => {
  const expanded = button.getAttribute("aria-expanded") === "true" || false;
  button.setAttribute("aria-expanded", !expanded);

  const menu_open_icon = document.getElementById("menu-opener");
  const menu_close_icon = document.getElementById("menu-closer");

  const largeScreenClass =
    "hidden md:flex md:space-x-8 font-semibold text-grey-200 hover:text-blue-800";
  const smallScreenClass =
    "absolute mt-24 border-t-2 z-0 inset-0 min-h-screen bg-yellow-300 place-items-center flex flex-col md:space-x-8 text-blue-900 space-y-10 py-20";

  if (!expanded) {
    menu_open_icon.classList.add("hidden");
    menu_close_icon.classList.remove("hidden");

    show.classList.remove("animate-fade-out");
    show.classList.add("animate-fade-in");
    setTimeout(() => {
      show.classList.remove("animate-fade-in");
    }, 500);

    largeScreenClass.split(" ").forEach((item) => show.classList.remove(item));
    smallScreenClass.split(" ").forEach((item) => show.classList.add(item));
  } else {
    menu_open_icon.classList.remove("hidden");
    menu_close_icon.classList.add("hidden");

    show.classList.remove("animate-fade-in");
    show.classList.add("animate-fade-out");
    setTimeout(() => {
      show.classList.remove("animate-fade-out");
    }, 500);

    smallScreenClass.split(" ").forEach((item) => show.classList.remove(item));
    largeScreenClass.split(" ").forEach((item) => show.classList.add(item));
  }
});

const exploreSelect = document.getElementById("exploreSelect");
const tip_p1 = document.getElementById("tip-p1");
const tip_p2 = document.getElementById("tip-p2");

const mostactive_tip_p1 =
  "Think of the stock market like a marketplace where people are buying and selling shares of different companies. When a stock has high trading volume, it means there are a lot of buyers and sellers interested in that particular stock. This is a good thing for investors because it means they can buy or sell shares more easily without affecting the price of the stock too much.";
const mostactive_tip_p2 =
  "Stocks with high trading volume can be a good investment choice because they offer liquidity, market efficiency, and price discovery";

const infocus_tip_p1 =
  "Trading stocks with the most news mentions may be advantageous for some traders because it can provide insights into market sentiment and help identify stocks that are gaining attention and popularity among investors. This can potentially drive up demand and increase the price of the stock, making it a profitable trade.";

const infocus_tip_p2 =
  "However, news sentiment can sometimes be biased or inaccurate, leading to misinterpretation and misjudgment of market trends. Additionally, high news mentions do not necessarily correlate with stock performance or value, and other factors such as financial reports and company fundamentals should also be considered. Finally, news reports can be driven by short-term events and hype, which can cause volatility and uncertainty in the market.";

const gainers_tip_p1 =
  "Trading top gaining stocks of the day can potentially yield high returns in a short amount of time, as these stocks have demonstrated strong upward momentum and may continue to rise in value. This strategy can also be appealing to short-term traders who are looking to make quick profits.";
const gainers_tip_p2 =
  "The main disadvantage of trading top gaining stocks of the day is that it can be highly volatile and unpredictable. While there is potential for significant gains, there is also a high risk of significant losses. The gains made by these stocks may be due to short-term factors, such as market hype, speculation, or news events, rather than underlying business fundamentals. As a result, it can be difficult to predict whether the gains will continue or whether the stock will experience a sharp decline in value.";

const losers_tip_p1 =
  "One potential advantage of trading losing stocks of the day is that they may be undervalued and have potential for a rebound in the future. By buying these stocks at a lower price, traders may be able to profit if the stock price increases in the future. Additionally, selling pressure on these stocks may create a buying opportunity for traders looking to enter the market at a lower price.";

const losers_tip_p2 =
  "However, the disadvantage is that they may continue to decline in value, leading to losses for the trader. This can happen if the stock is experiencing a significant negative event or trend that is not yet fully reflected in its price. Additionally, stocks that are losing value may be subject to panic selling, which can exacerbate their decline and make it difficult for a trader to exit the position at a favorable price";

exploreSelect.addEventListener("change", (event) => {
  const option = event.target.value;

  switch (option) {
    case "mostactive":
      tip_p1.textContent = mostactive_tip_p1;
      tip_p2.textContent = mostactive_tip_p2;
      break;
    case "mootley":
      tip_p1.textContent = mootley_tip_p1;
      tip_p2.textContent = mootley_tip_p2;
      break;
    case "infocus":
      tip_p1.textContent = infocus_tip_p1;
      tip_p2.textContent = infocus_tip_p2;
      break;
    case "gainers":
      tip_p1.textContent = gainers_tip_p1;
      tip_p2.textContent = gainers_tip_p2;
      break;
  }
});

const submitBtn = document.getElementById("submit-btn");

// Add an event listener to the form's submit event
document.getElementById("my-form").addEventListener("submit", function () {
  // Disable the submit button to prevent multiple submissions
  submitBtn.disabled = true;
});
