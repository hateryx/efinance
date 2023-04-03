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

const mootley_tip_p1 =
  "Motley Fool is a multimedia financial-services company that provides stock recommendations and investment advice to its subscribers.";
const mootley_tip_p2 =
  "The company does research on companies and markets to help investors make informed investment decisions. They also have a track record of recommending stocks that have led to significant returns for investors. For example, the company has recommended stocks such as Amazon, Apple, and Netflix before they became some of the largest companies in the world.";

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
  }
});
