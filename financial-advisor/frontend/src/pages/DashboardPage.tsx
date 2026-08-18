import { Box, Button, Flex, Stack, Text, useToast, Container, Icon } from '@chakra-ui/react';
import { useAuth } from '../context/AuthContext';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Inline icon components (no external icon library dependency required)
const FolderIcon = (props: { boxSize?: number; color?: string }) => (
  <Icon viewBox="0 0 24 24" {...props}>
    <path
      fill="currentColor"
      d="M10 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-8l-2-2Z"
    />
  </Icon>
);

const TrendingUpIcon = (props: { boxSize?: number; color?: string }) => (
  <Icon viewBox="0 0 24 24" {...props}>
    <path
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M3 17l6-6 4 4 8-8M17 7h4v4"
    />
  </Icon>
);

const ZapIcon = (props: { boxSize?: number; color?: string }) => (
  <Icon viewBox="0 0 24 24" {...props}>
    <path
      fill="currentColor"
      d="M13 2 3 14h7l-1 8 10-12h-7l1-8Z"
    />
  </Icon>
);

interface Holding { ticker: string; shares: number; cost_basis: number; }

type IconRenderer = (props: { boxSize?: number; color?: string }) => JSX.Element;

const StatCard = ({ icon, label, value, sub, subColor }: { icon: IconRenderer; label: string; value: string; sub: string; subColor?: string }) => (
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
    <Box mb={2}>{icon({ boxSize: 5, color: 'brand.400' })}</Box>
    <Text fontSize="sm" fontWeight="medium" color="gray.500">
      {label}
    </Text>
    <Text fontSize="3xl" fontWeight="bold" mt={1} color="white">
      {value}
    </Text>
    <Text fontSize="sm" color={subColor || 'gray.500'} mt={1}>
      {sub}
    </Text>
  </Box>
);

const ActionTile = ({ label, sub, onClick, variant }: { label: string; sub: string; onClick?: () => void; variant: 'solid' | 'outline' }) => (
  <Box
    className={`action-tile ${variant === 'solid' ? '' : 'glass'}`}
    flex="1"
    minW="220px"
    borderRadius="xl"
    p={5}
    cursor="pointer"
    onClick={onClick}
    border="1px solid"
    borderColor={variant === 'solid' ? 'transparent' : 'surface.border'}
    bgGradient={variant === 'solid' ? 'linear(to-r, brand.500, brand.600)' : undefined}
    transition="all 0.2s"
    _hover={{ transform: 'translateY(-2px)', borderColor: variant === 'outline' ? 'brand.400' : undefined, opacity: variant === 'solid' ? 0.92 : 1 }}
  >
    <Text fontWeight="bold" color="white" fontSize="lg">{label}</Text>
    <Text fontSize="sm" color={variant === 'solid' ? 'blue.100' : 'gray.500'} mt={1}>{sub}</Text>
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
    <Container maxW="1200px" py={4} px={{ base: 4, md: 6 }}>
      <Stack spacing={8}>
        <Box>
          <Text className="dash-greeting" mb={1}>Welcome back</Text>
          <Text fontSize="3xl" fontWeight="bold" color="white">
            Dashboard
          </Text>
        </Box>

        <Flex gap={4} flexWrap="wrap">
          <StatCard
            icon={FolderIcon}
            label="Portfolio Value"
            value={`$${invested.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
            sub="Total cost basis"
            subColor="blue.200"
          />
          <StatCard icon={TrendingUpIcon} label="Tracked Assets" value={`${holdings.length}`} sub="Active portfolio positions" />
          <StatCard icon={ZapIcon} label="Advisor Status" value="Online" sub="Market intelligence ready" subColor="blue.200" />
        </Flex>

        <Box>
          <Text fontSize="sm" fontWeight="semibold" color="gray.400" mb={3} textTransform="uppercase" letterSpacing="wide">
            Quick actions
          </Text>
          <Flex gap={4} flexWrap="wrap">
            <ActionTile label="View Portfolio" sub="Review holdings & performance" variant="solid" onClick={() => navigate('/portfolio')} />
            <ActionTile label="Start Chat" sub="Ask your AI advisor a question" variant="solid" onClick={() => navigate('/chat')} />
            <ActionTile label="Market Analysis" sub="Coming soon" variant="outline" />
          </Flex>
        </Box>
      </Stack>
    </Container>
  );
};

export default DashboardPage;