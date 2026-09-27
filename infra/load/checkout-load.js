import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

const CHECKOUT_DURATION = new Trend("cdr_checkout_duration", true);
const CHECKOUT_FAILED = new Rate("cdr_checkout_failed");
const CHECKOUT_REQUESTS = new Counter("cdr_checkout_requests");
const VUS = Number.parseInt(__ENV.CDR_VUS || "200", 10);
const DURATION_S = Number.parseInt(__ENV.CDR_DURATION_S || "120", 10);

export const options = {
  scenarios: {
    checkout_load: {
      executor: "constant-vus",
      vus: VUS,
      duration: `${DURATION_S}s`,
    },
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";
const PRODUCT_ID = "OLJCESPC7Z";

export default function () {
  const jar = http.cookieJar();
  jar.set(BASE_URL, "session_id", `${__VU}-${__ITER}`);

  const home = http.get(`${BASE_URL}/`);
  check(home, { "home 200": (response) => response.status === 200 });

  const addToCart = http.post(`${BASE_URL}/cart`, {
    product_id: PRODUCT_ID,
    quantity: "1",
  });
  check(addToCart, { "cart add accepted": (response) => response.status < 400 });

  const checkout = http.post(`${BASE_URL}/cart/checkout`, {
    email: "loadtest@example.com",
    street_address: "1600 Amphitheatre Parkway",
    zip_code: "94043",
    city: "Mountain View",
    state: "CA",
    country: "United States",
    credit_card_number: "4432801561520454",
    credit_card_expiration_month: "1",
    credit_card_expiration_year: "2039",
    credit_card_cvv: "672",
  });
  CHECKOUT_DURATION.add(checkout.timings.duration);
  CHECKOUT_FAILED.add(checkout.status !== 200);
  CHECKOUT_REQUESTS.add(1);
  check(checkout, { "checkout completed": (response) => response.status === 200 });

  sleep(1);
}
