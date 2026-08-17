import { Box, Button, Flex, Stack, Text, useToast } from '@chakra-ui/react';
import { useAuth } from '../context/AuthContext';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface Holding { ticker: string; shares: number; cost_basis: number; }

const StatCard = ({ label, value, sub, subColor }: { label: string; value: string; sub: string; subColor?: string }) => (
  <Box
    flex="1"
    minW="220px"
    className="glass"
    border="1px solid"
    borderColor="surface.border"
    borderRadius="xl"
    p={5}
    transition="all 0.2s"
    _hover={{ borderColor: 'brand.400', transform: 'translateY(-2px)' }}
  >
    <Text fontSize="sm" fontWeight="medium" color="gray.500">
      {label}
    </Text>
    <Text fontSize="3xl" fontWeight="bold" mt={2} color="white">
      {value}
    </Text>
    <Text fontSize="sm" color={subColor || 'gray.500'} mt={1}>
      {sub}
    </Text>
  </Box>
);

const DashboardPage = () => {
  const { currentUser } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [holdings, setHoldings] = useState<Holding[]>([]);

  useEffect(() => {
    const fetchHoldings = async () => {
      try {
        const response = await fetch('http://localhost:8000/users/me/portfolio', {
          headers: { Authorization: `Bearer ${currentUser?.token}` },
        });
        if (!response.ok) throw new Error('Failed to fetch portfolio');
        setHoldings(await response.json());
      } catch (error) {
        console.error('Error fetching portfolio:', error);
        toast({ title: 'Failed to load dashboard data', status: 'error', duration: 3000, isClosable: true });
      }
    };
    if (currentUser) fetchHoldings();
  }, [currentUser, toast]);

  const invested = holdings.reduce((sum, holding) => sum + holding.shares * holding.cost_basis, 0);

  return (
    <Box py={4}>
      <Stack spacing={8}>
        <Text fontSize="3xl" fontWeight="bold" color="white">
          Dashboard
        </Text>

        <Flex gap={4} flexWrap="wrap">
          <StatCard
            label="Portfolio Value"
            value={`$${invested.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
            sub="Total cost basis"
            subColor="blue.200"
          />
          <StatCard label="Tracked Assets" value={`${holdings.length}`} sub="Active portfolio positions" />
          <StatCard label="Advisor Status" value="Online" sub="Market intelligence ready" subColor="blue.200" />
        </Flex>

        <Flex mt={4} gap={4} flexWrap="wrap" justify="center">
          <Button
            flex="1"
            minW="220px"
            size="lg"
            bgGradient="linear(to-r, brand.500, brand.600)"
            color="white"
            _hover={{ bgGradient: 'linear(to-r, brand.400, brand.500)' }}
            onClick={() => navigate('/portfolio')}
          >
            View Portfolio
          </Button>
          <Button
            flex="1"
            minW="220px"
            size="lg"
            bgGradient="linear(to-r, brand.500, brand.400)"
            color="white"
            _hover={{ opacity: 0.9 }}
            onClick={() => navigate('/chat')}
          >
            Start Chat
          </Button>
          <Button
            flex="1"
            minW="220px"
            size="lg"
            variant="outline"
            borderColor="surface.border"
            color="gray.200"
            _hover={{ borderColor: 'brand.400', color: 'brand.300' }}
          >
            Market Analysis
          </Button>
        </Flex>
      </Stack>
    </Box>
  );
};

export default DashboardPage;
