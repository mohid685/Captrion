import { Box, Button, Flex, Stack, Text } from '@chakra-ui/react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const features = [
  { icon: '🤖', title: 'Agentic AI', desc: 'Advanced AI agents that reason and act on your behalf' },
  { icon: '📊', title: 'Portfolio Management', desc: 'Track, analyze, and optimize your investments' },
  { icon: '📈', title: 'Market Analysis', desc: 'Real-time insights and predictions' },
  { icon: '🛡️', title: 'Risk Management', desc: 'Protect your portfolio with intelligent risk controls' },
];

const HomePage = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate(currentUser ? '/dashboard' : '/login');
  };

  return (
    <Box minH="80vh" py={10} px={4}>
      <Stack spacing={8} align="center" maxW="4xl" mx="auto">
        <Box
          className="glass"
          border="1px solid"
          borderColor="surface.border"
          borderRadius="2xl"
          boxShadow="0 20px 60px rgba(43,188,255,0.15)"
          p={{ base: 6, md: 10 }}
          w="100%"
          textAlign="center"
        >
          <Box
            w={16}
            h={16}
            mx="auto"
            mb={6}
            borderRadius="xl"
            bgGradient="linear(to-br, brand.400, brand.700)"
            display="flex"
            alignItems="center"
            justifyContent="center"
            fontSize="3xl"
            fontWeight="bold"
            color="white"
          >
            C
          </Box>
          <Text
            fontSize={{ base: '3xl', md: '5xl' }}
            fontWeight="extrabold"
            bgGradient="linear(to-r, brand.300, brand.500)"
            bgClip="text"
          >
            Captrion
          </Text>
          <Text fontSize={{ base: 'lg', md: '2xl' }} color="gray.300" mt={2} fontWeight="medium">
            Market research, made simple
          </Text>
          <Text fontSize="md" mt={4} color="gray.500" maxW="xl" mx="auto">
            Get personalized investment advice, portfolio management, and market insights
            powered by advanced AI agents.
          </Text>

          <Flex mt={8} gap={4} justify="center" flexWrap="wrap">
            <Button
              bgGradient="linear(to-r, brand.500, brand.600)"
              color="white"
              _hover={{ bgGradient: 'linear(to-r, brand.400, brand.600)', transform: 'translateY(-2px)' }}
              transition="all 0.2s"
              onClick={handleGetStarted}
              px={8}
              py={6}
              fontSize="lg"
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
              fontSize="lg"
            >
              Try the Chat
            </Button>
          </Flex>

          <Flex mt={12} gap={5} justify="center" flexWrap="wrap">
            {features.map((f) => (
              <Box
                key={f.title}
                textAlign="left"
                minW="220px"
                flex="1"
                className="glass"
                border="1px solid"
                borderColor="surface.border"
                borderRadius="xl"
                p={5}
                transition="all 0.2s"
                _hover={{ borderColor: 'brand.400', transform: 'translateY(-3px)' }}
              >
                <Text fontSize="2xl" mb={2}>{f.icon}</Text>
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
      </Stack>
    </Box>
  );
};

export default HomePage;
