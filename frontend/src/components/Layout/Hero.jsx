export default function Hero() {
  return (
    <section className="max-w-7xl mx-auto px-6 py-20 grid md:grid-cols-2 gap-12 items-center">
      <div>
        <h2 className="text-4xl font-bold mb-6">
          Fast & Secure Money Transfers for Africa
        </h2>
        <p className="text-gray-600 mb-8">
          Pal’s Pay lets individuals and businesses send, receive, and manage
          money instantly — with low fees and bank-grade security.
        </p>

        <div className="flex gap-4">
          <a
            href="#"
            className="bg-green-600 text-white px-6 py-3 rounded-md hover:bg-green-700"
          >
            Get Started
          </a>
          <a
            href="#"
            className="border border-green-600 text-green-600 px-6 py-3 rounded-md"
          >
            Learn More
          </a>
        </div>
      </div>

      <div className="rounded-xl overflow-hidden shadow-lg">
        <video controls className="w-full">
          <source src="/promo-video.mp4" type="video/mp4" />
        </video>
      </div>
    </section>
  );
}