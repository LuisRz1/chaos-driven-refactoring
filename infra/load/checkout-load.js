import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    checkout_load: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "20s", target: 120 },
        { duration: "60s", target: 200 },
        { duration: "30s", target: 200 },
        { duration: "10s", target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.05"],
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
  check(checkout, { "checkout completed": (response) => response.status === 200 });

  sleep(1);
}
