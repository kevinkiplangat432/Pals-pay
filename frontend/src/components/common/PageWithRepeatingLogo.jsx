export default function PageWithRepeatingLogo({ children, className = '' }) {
  return (
    <div className={`relative ${className}`}>
      <div 
        className="fixed inset-0 pointer-events-none z-0"
        style={{
          backgroundImage: 'url(/palslogo.png)',
          backgroundRepeat: 'repeat',
          backgroundSize: '200px',
          opacity: 0.08
        }}
      />
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}
