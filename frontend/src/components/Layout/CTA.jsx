import { Link } from "react-router-dom";

export default function CTA() {
  return (
    <section className="bg-green-600 text-white text-center py-20 px-6">
      <h3 className="text-3xl font-bold mb-4">
        Start Sending & Receiving Money Today
      </h3>
      <p className="mb-8">
        Create your Pal’s Pay account in minutes.
      </p>
      <Link
        to="/signup"
        className="bg-white text-green-600 px-8 py-3 rounded-md font-semibold"
      >
        Create Free Account
      </Link>
    </section>
  );
}
