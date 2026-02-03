const features = [
  {
    title: "Instant Transfers",
    desc: "Move money in seconds, 24/7."
  },
  {
    title: "Low Transaction Fees",
    desc: "Designed to be affordable for everyone."
  },
  {
    title: "Secure Payments",
    desc: "Built with modern encryption and security standards."
  },
  {
    title: "Business Ready",
    desc: "Perfect for merchants, freelancers, and startups."
  }
];

export default function Features() {
  return (
    <section className="bg-white py-20">
      <div className="max-w-7xl mx-auto px-6">
        <h3 className="text-3xl font-bold text-center mb-12">
          Why Choose Pal’s Pay?
        </h3>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((f, i) => (
            <div
              key={i}
              className="border rounded-xl p-6 bg-gray-50 hover:shadow-md transition"
            >
              <h4 className="font-semibold text-lg mb-2">{f.title}</h4>
              <p className="text-gray-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
