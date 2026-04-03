const HeroSection = (): React.JSX.Element => {
  return (
    <section className="bg-white py-16 px-4">
      <div className="container mx-auto max-w-6xl text-center">
        <span className="inline-block bg-primary/10 text-primary text-sm font-semibold px-4 py-2 rounded-full mb-6">
          Trial Program
        </span>
        
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-secondary mb-6 leading-tight">
          Claim Sertifikat{' '}
          <span className="text-primary">Trial Bootcamp</span>
          <br />
          Intelligo ID
        </h1>
        
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Upload project kamu dan dapatkan sertifikat resmi sebagai bukti 
          partisipasi dalam program trial bootcamp Data Science & AI
        </p>
      </div>
    </section>
  )
}

export default HeroSection
