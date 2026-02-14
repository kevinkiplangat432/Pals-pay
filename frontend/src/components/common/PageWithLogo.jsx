export default function PageWithLogo({ children, className = '' }) {
  return (
    <div className={`relative ${className}`}>
      <div 
        className="fixed inset-0 flex items-center justify-center pointer-events-none z-0"
        style={{
          backgroundImage: 'url(/palslogo.png)',
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'center',
          backgroundSize: '40%',
          opacity: 0.03
        }}
      />
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}
