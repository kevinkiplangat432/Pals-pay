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

  const toggle = (index) => {
    setOpenIndex(openIndex === index ? null : index);
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
    </div>
  );
};

export default FAQs;