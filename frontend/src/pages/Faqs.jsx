import React, { useState } from "react";

const faqsData = [
  {
    question: "How do I create an account?",
    answer: "Click on the Signup link in the navbar, fill in your details, and submit the form."
  },
  {
    question: "How do I reset my password?",
    answer: "Go to the Login page and click 'Forgot Password'. Follow the instructions sent to your email."
  },
  {
    question: "How can I contact support?",
    answer: "You can contact support via the contact form on the website or email us at support@example.com."
  },
  {
    question: "What currencies are supported?",
    answer: "Currently, we support KES, USD, and many other european and african currencies."
  },
];

const FAQs = () => {
  const [openIndex, setOpenIndex] = useState(null);
  const [contactForm, setContactForm] = useState({ name: "", email: "", message: "" });
  const [submitStatus, setSubmitStatus] = useState("");

  const toggle = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  const handleContactSubmit = async (e) => {
    e.preventDefault();
    setSubmitStatus("sending");
    
    try {
      const response = await fetch("http://localhost:5000/api/v1/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(contactForm),
      });
      
      if (response.ok) {
        setSubmitStatus("success");
        setContactForm({ name: "", email: "", message: "" });
      } else {
        setSubmitStatus("error");
      }
    } catch (error) {
      setSubmitStatus("error");
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6 text-gray-900">Frequently Asked Questions</h1>
      <div className="space-y-4">
        {faqsData.map((faq, index) => (
          <div key={index} className="border rounded-lg">
            <button
              onClick={() => toggle(index)}
              className="w-full text-left px-4 py-3 flex justify-between items-center font-medium bg-gray-100 hover:bg-gray-200"
            >
              {faq.question}
              <span>{openIndex === index ? "−" : "+"}</span>
            </button>
            {openIndex === index && (
              <div className="px-4 py-3 text-gray-700 bg-white border-t">{faq.answer}</div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-12 bg-green-50 rounded-2xl p-8 border border-green-200">
        <h2 className="text-2xl font-bold mb-4 text-gray-900">Have More Questions?</h2>
        <p className="text-gray-600 mb-6">Contact us and we'll get back to you as soon as possible.</p>
        
        {submitStatus === "success" && (
          <div className="mb-4 p-4 bg-green-100 text-green-800 rounded-lg">
            Message sent successfully! We'll get back to you soon.
          </div>
        )}
        
        {submitStatus === "error" && (
          <div className="mb-4 p-4 bg-red-100 text-red-800 rounded-lg">
            Failed to send message. Please try again.
          </div>
        )}
        
        <form onSubmit={handleContactSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Your Name"
            value={contactForm.name}
            onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
          <input
            type="email"
            placeholder="Your Email"
            value={contactForm.email}
            onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
          <textarea
            placeholder="Your Message"
            value={contactForm.message}
            onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
            required
            rows={5}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={submitStatus === "sending"}
            className="w-full bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 font-semibold disabled:opacity-50"
          >
            {submitStatus === "sending" ? "Sending..." : "Send Message"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default FAQs;