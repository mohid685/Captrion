import { Box, Button, Flex, Text } from '@chakra-ui/react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import captrionLogo from '../../logo/logo_C.png';

const features = [
  { icon: 'Bot', title: 'Agentic AI', desc: 'Advanced AI agents that reason and act on your behalf' },
  { icon: 'BarChart', title: 'Portfolio Management', desc: 'Track, analyze, and optimize your investments' },
  { icon: 'TrendingUp', title: 'Market Analysis', desc: 'Real-time insights and predictions' },
  { icon: 'Shield', title: 'Risk Management', desc: 'Protect your portfolio with intelligent risk controls' },
];

const stats = [
  { num: '24/7', label: 'Agent uptime' },
  { num: '<1s', label: 'Response time' },
  { num: 'Live', label: 'Market data' },
];

const HomePage = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate(currentUser ? '/dashboard' : '/login');
  };

  return (
    <Box py={{ base: 6, md: 10 }} px={{ base: 2, md: 4 }}>
      <Box className="home-shell">
        <Box className="home-visual">
          <Box className="auth-core">
            <Box className="auth-core-ring r1" />
            <Box className="auth-core-ring r2" />
            <Box className="auth-core-ring r3" />
            <Box className="auth-core-ticks" />
            <Box className="auth-core-hub">
              <Box className="auth-core-logo">
                <img src={captrionLogo} alt="Captrion" />
              </Box>
            </Box>
          </Box>
        </Box>

        <Box>
          <Box className="home-badge" mb={5}>
            <span />
            Agent online
          </Box>
          <Text className="home-title" mb={5}>
            Market research, <em>made simple</em>
          </Text>
          <Text className="home-sub" mb={8}>
            Get personalized investment advice, portfolio management, and market insights
            powered by advanced AI agents that watch the market so you don't have to.
          </Text>

          <Flex gap={4} flexWrap="wrap" mb={10}>
            <Button
              bgGradient="linear(to-r, brand.500, brand.600)"
              color="white"
              _hover={{ bgGradient: 'linear(to-r, brand.400, brand.600)', transform: 'translateY(-2px)' }}
              transition="all 0.2s"
              onClick={handleGetStarted}
              px={8}
              py={6}
              fontSize="md"
            >
              Get Started
            </Button>
            <Button
              variant="outline"
              borderColor="surface.border"
              color="gray.200"
              _hover={{ borderColor: 'brand.400', color: 'brand.300' }}
              onClick={() => navigate('/chat')}
              px={8}
              py={6}
              fontSize="md"
            >
              Try the Chat
            </Button>
          </Flex>

          <Flex className="home-stats">
            {stats.map((s) => (
              <Box key={s.label}>
                <Text className="stat-num">{s.num}</Text>
                <Text className="stat-label">{s.label}</Text>
              </Box>
            ))}
          </Flex>
        </Box>
      </Box>

      <Flex mt={{ base: 6, md: 10 }} gap={5} flexWrap="wrap">
        {features.map((f) => (
          <Box
            key={f.title}
            className="glass feature-card"
            textAlign="left"
            minW="220px"
            flex="1"
            border="1px solid"
            borderColor="surface.border"
            borderRadius="xl"
            p={5}
            transition="all 0.2s"
            _hover={{ borderColor: 'brand.400', transform: 'translateY(-3px)' }}
          >
            <Box className="feature-icon">{f.icon}</Box>
            <Text fontSize="md" fontWeight="semibold" color="white">
              {f.title}
            </Text>
            <Text fontSize="sm" color="gray.500" mt={1}>
              {f.desc}
            </Text>
          </Box>
        ))}
      </Flex>
    </Box>
  );
};

export default HomePage;