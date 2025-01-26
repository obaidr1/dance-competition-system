import styled from 'styled-components';

export const Container = styled.div`
  min-height: 100vh;
  background-color: #121212;
  color: #ffffff;
`;

export const Hero = styled.section`
  padding: 6rem 2rem;
  text-align: center;
  background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)),
              url('/images/dance-bg.jpg') center/cover;
  
  @media (max-width: 768px) {
    padding: 4rem 1rem;
  }
`;

export const Title = styled.h1`
  font-size: 4rem;
  font-weight: 700;
  margin-bottom: 2rem;
  background: linear-gradient(45deg, #2196F3, #00BCD4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  
  @media (max-width: 768px) {
    font-size: 2.5rem;
  }
`;

export const Navigation = styled.nav`
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin: 2rem 0;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
  }
`;

export const NavLink = styled.a`
  color: #ffffff;
  text-decoration: none;
  font-size: 1.1rem;
  padding: 0.5rem 1rem;
  transition: all 0.3s ease;
  border-bottom: 2px solid transparent;
  
  &:hover {
    border-bottom-color: #2196F3;
  }
`;

export const FeaturesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;
  max-width: 1200px;
  margin: 4rem auto;
  padding: 0 2rem;
  
  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @media (max-width: 576px) {
    grid-template-columns: 1fr;
  }
`;

export const FeatureCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 1rem;
  padding: 2rem;
  text-align: center;
  transition: transform 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
  
  &:hover {
    transform: translateY(-10px);
    border-color: #2196F3;
  }
`;

export const Icon = styled.i`
  font-size: 2.5rem;
  color: #2196F3;
  margin-bottom: 1.5rem;
`;

export const CardTitle = styled.h3`
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: #ffffff;
`;

export const CardText = styled.p`
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.6;
`;

export const StepsSection = styled.section`
  max-width: 1200px;
  margin: 6rem auto;
  padding: 0 2rem;
`;

export const StepsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  margin-top: 3rem;
  
  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @media (max-width: 576px) {
    grid-template-columns: 1fr;
  }
`;

export const StepCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 1rem;
  padding: 2rem;
  text-align: center;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.1);
  
  &:hover {
    border-color: #2196F3;
  }
`;

export const StepNumber = styled.div`
  width: 40px;
  height: 40px;
  background: #2196F3;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  font-weight: bold;
  margin: 0 auto 1.5rem;
`;

export const Button = styled.a`
  display: inline-block;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 500;
  color: #ffffff;
  background: linear-gradient(45deg, #2196F3, #00BCD4);
  border-radius: 2rem;
  text-decoration: none;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(33, 150, 243, 0.3);
  }
  
  @media (max-width: 768px) {
    width: 100%;
    text-align: center;
  }
`;
