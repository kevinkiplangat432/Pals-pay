import { Link } from "react-router-dom";

export default function Hero() {
  return (
    <section className="w-full py-20 bg-white">
      <div className="mx-auto w-full px-4 sm:px-6 md:px-8 lg:px-12 xl:px-16 grid md:grid-cols-2 gap-12 items-center max-w-[1600px]">
        
        {/* Left Column: Text */}
        <div className="space-y-6 md:max-w-lg">
          <h2 className="text-4xl md:text-5xl font-bold leading-tight">
            Fast & Secure Money Transfers for the Modern World
          </h2>

          <p className="text-gray-600 text-lg leading-relaxed">
            Pal’s Pay lets individuals and businesses send, receive, and manage
            money instantly — with low fees and bank-grade security.
          </p>

          <div className="flex flex-wrap gap-4">
            <Link
              to="/signup"
              className="bg-green-600 text-white px-6 py-3 rounded-md hover:bg-green-700"
            >
              Get Started
            </Link>
            <Link
              to="/faqs"
              className="border border-green-600 text-green-600 px-6 py-3 rounded-md"
            >
              Learn More
            </Link>
          </div>
        </div>

        {/* Right Column: Logo Display */}
        <div className="rounded-xl overflow-hidden aspect-video max-h-[450px] md:max-h-[500px] bg-white flex items-center justify-center">
          <img src="/palslogo.png" alt="PalsPay" className="w-3/4 h-auto object-contain" />
        </div>

        {/* Right Column: Video (Commented Out) */}
        {/* <div className="rounded-xl overflow-hidden shadow-lg aspect-video max-h-[450px] md:max-h-[500px]">
          <video controls className="w-full h-full object-cover">
            <source src="/promo-video.mp4" type="video/mp4" />
          </video>
        </div> */}
      </div>
    </section>
  );
}
