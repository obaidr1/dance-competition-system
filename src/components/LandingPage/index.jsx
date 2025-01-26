import React from 'react';
import {
  Container,
  Hero,
  Title,
  Navigation,
  NavLink,
  FeaturesGrid,
  FeatureCard,
  Icon,
  CardTitle,
  CardText,
  StepsSection,
  StepsGrid,
  StepCard,
  StepNumber,
  Button
} from './styles';

const features = [
  {
    icon: 'fas fa-users',
    title: 'Admin Panel',
    description: 'Effortlessly manage competitions, dancers, and rounds.'
  },
  {
    icon: 'fas fa-star',
    title: 'Judging Panel',
    description: 'Simple, intuitive scoring for judges.'
  },
  {
    icon: 'fas fa-chart-line',
    title: 'Real-Time Results',
    description: 'Display scores dynamically for participants and audiences.'
  },
  {
    icon: 'fas fa-sliders-h',
    title: 'Customizable Settings',
    description: 'Tailor rounds, music, and levels to your needs.'
  }
];

const steps = [
  {
    number: 1,
    title: 'Create a Competition',
    description: 'Set up rounds, add dancers, and configure judging criteria.'
  },
  {
    number: 2,
    title: 'Score and Manage',
    description: 'Judges score performances while admins manage the flow.'
  },
  {
    number: 3,
    title: 'View Results',
    description: 'Get instant results and detailed competition insights.'
  }
];

const LandingPage = () => {
  return (
    <Container>
      <Hero>
        <Title>Everything You Need in One Platform</Title>
        <Navigation>
          <NavLink href="#features">Features</NavLink>
          <NavLink href="#how-it-works">How It Works</NavLink>
          <NavLink href="#testimonials">Testimonials</NavLink>
          <NavLink href="#pricing">Pricing</NavLink>
          <NavLink href="#faq">FAQ</NavLink>
        </Navigation>
      </Hero>

      <FeaturesGrid id="features">
        {features.map((feature, index) => (
          <FeatureCard key={index}>
            <Icon className={feature.icon} />
            <CardTitle>{feature.title}</CardTitle>
            <CardText>{feature.description}</CardText>
          </FeatureCard>
        ))}
      </FeaturesGrid>

      <StepsSection id="how-it-works">
        <Title>How It Works in 3 Simple Steps</Title>
        <StepsGrid>
          {steps.map((step, index) => (
            <StepCard key={index}>
              <StepNumber>{step.number}</StepNumber>
              <CardTitle>{step.title}</CardTitle>
              <CardText>{step.description}</CardText>
            </StepCard>
          ))}
        </StepsGrid>
      </StepsSection>

      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <Button href="/register">Get Started for Free</Button>
      </div>
    </Container>
  );
};

export default LandingPage;
