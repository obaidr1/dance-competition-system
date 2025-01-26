import React from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  Event as EventIcon,
  EmojiEvents as TrophyIcon,
  Schedule as ScheduleIcon,
  Group as GroupIcon,
} from '@mui/icons-material';

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  backgroundColor: 'rgba(255, 255, 255, 0.05)',
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(255, 255, 255, 0.1)',
}));

const StyledCard = styled(Card)(({ theme }) => ({
  height: '100%',
  backgroundColor: 'rgba(255, 255, 255, 0.05)',
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(255, 255, 255, 0.1)',
  transition: 'transform 0.2s',
  '&:hover': {
    transform: 'translateY(-5px)',
  },
}));

const UserDashboard = () => {
  const upcomingCompetitions = [
    {
      id: 1,
      name: 'Summer Dance Festival',
      date: '2025-06-15',
      location: 'New York',
      category: 'Latin',
    },
    {
      id: 2,
      name: 'International Ballet Competition',
      date: '2025-07-01',
      location: 'London',
      category: 'Ballet',
    },
  ];

  const recentResults = [
    {
      id: 1,
      competition: 'Spring Dance Championship',
      place: '1st',
      category: 'Contemporary',
      date: '2025-03-20',
    },
    {
      id: 2,
      competition: 'Regional Dance Contest',
      place: '2nd',
      category: 'Jazz',
      date: '2025-02-15',
    },
  ];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        {/* Welcome Section */}
        <Grid item xs={12}>
          <StyledPaper>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h4" color="primary" gutterBottom>
                Welcome back, Dancer!
              </Typography>
              <Button variant="contained" color="primary">
                Register for Competition
              </Button>
            </Box>
          </StyledPaper>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12} md={3}>
          <StyledCard>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Competitions
              </Typography>
              <Typography variant="h3" color="primary">
                12
              </Typography>
            </CardContent>
          </StyledCard>
        </Grid>
        <Grid item xs={12} md={3}>
          <StyledCard>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Medals
              </Typography>
              <Typography variant="h3" color="primary">
                8
              </Typography>
            </CardContent>
          </StyledCard>
        </Grid>
        <Grid item xs={12} md={3}>
          <StyledCard>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Categories
              </Typography>
              <Typography variant="h3" color="primary">
                4
              </Typography>
            </CardContent>
          </StyledCard>
        </Grid>
        <Grid item xs={12} md={3}>
          <StyledCard>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Partners
              </Typography>
              <Typography variant="h3" color="primary">
                3
              </Typography>
            </CardContent>
          </StyledCard>
        </Grid>

        {/* Upcoming Competitions */}
        <Grid item xs={12} md={6}>
          <StyledPaper>
            <Typography variant="h6" gutterBottom>
              Upcoming Competitions
            </Typography>
            <List>
              {upcomingCompetitions.map((competition) => (
                <ListItem key={competition.id}>
                  <ListItemIcon>
                    <EventIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary={competition.name}
                    secondary={`${competition.date} | ${competition.location} | ${competition.category}`}
                  />
                </ListItem>
              ))}
            </List>
          </StyledPaper>
        </Grid>

        {/* Recent Results */}
        <Grid item xs={12} md={6}>
          <StyledPaper>
            <Typography variant="h6" gutterBottom>
              Recent Results
            </Typography>
            <List>
              {recentResults.map((result) => (
                <ListItem key={result.id}>
                  <ListItemIcon>
                    <TrophyIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary={result.competition}
                    secondary={`${result.place} Place | ${result.category} | ${result.date}`}
                  />
                </ListItem>
              ))}
            </List>
          </StyledPaper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default UserDashboard;
