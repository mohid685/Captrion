import { Box, Button, Flex, Stack, Text, useToast, Table, Tbody, Td, Th, Thead, Tr, Spinner } from '@chakra-ui/react';
import { useAuth } from '../context/AuthContext';
import { useEffect, useState } from 'react';

interface Holding {
  ticker: string;
  shares: number;
  cost_basis: number;
}

const PortfolioPage = () => {
  const { currentUser } = useAuth();
  const toast = useToast();
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchHoldings = async () => {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:8000/users/me/portfolio', {
          headers: { Authorization: `Bearer ${currentUser?.token}` },
        });

        if (!response.ok) throw new Error('Failed to fetch portfolio');

        const data = await response.json();
        setHoldings(data);
      } catch (error) {
        console.error('Error fetching portfolio:', error);
        toast({ title: 'Failed to load portfolio', status: 'error', duration: 3000, isClosable: true });
      } finally {
        setLoading(false);
      }
    };

    if (currentUser) fetchHoldings();
  }, [currentUser, toast]);

  const handleAddHolding = () => {
    toast({ title: 'Add holding feature coming soon', status: 'info', duration: 3000, isClosable: true });
  };

  const totalInvested = holdings.reduce((sum, h) => sum + h.shares * h.cost_basis, 0);
  const totalShares = holdings.reduce((sum, h) => sum + h.shares, 0);

  return (
    <Box py={4}>
      <Stack spacing={6}>
        <Box>
          <Text className="dash-greeting" mb={1}>Your holdings</Text>
          <Text fontSize="3xl" fontWeight="bold" color="white">
            My Portfolio
          </Text>
        </Box>

        {holdings.length > 0 && (
          <Flex className="portfolio-summary">
            <Box className="glass portfolio-chip" border="1px solid" borderColor="surface.border">
              <Text className="chip-label">Total invested</Text>
              <Text className="chip-value">${totalInvested.toLocaleString(undefined, { maximumFractionDigits: 2 })}</Text>
            </Box>
            <Box className="glass portfolio-chip" border="1px solid" borderColor="surface.border">
              <Text className="chip-label">Positions</Text>
              <Text className="chip-value">{holdings.length}</Text>
            </Box>
            <Box className="glass portfolio-chip" border="1px solid" borderColor="surface.border">
              <Text className="chip-label">Total shares</Text>
              <Text className="chip-value">{totalShares}</Text>
            </Box>
          </Flex>
        )}

        <Box
          className="glass"
          border="1px solid"
          borderColor="surface.border"
          borderRadius="xl"
          p={5}
          w="100%"
          overflowX="auto"
        >
          <Flex align="center" justify="space-between" mb={4}>
            <Text fontSize="lg" fontWeight="semibold" color="white">
              Holdings
            </Text>
            <Button
              variant="outline"
              borderColor="brand.400"
              color="blue.200"
              _hover={{ bg: 'rgba(43,188,255,0.14)' }}
              onClick={handleAddHolding}
              size="sm"
            >
              + Add Holding
            </Button>
          </Flex>

          {loading ? (
            <Flex justify="center" py={10}>
              <Spinner color="brand.400" />
            </Flex>
          ) : holdings.length === 0 ? (
            <Box textAlign="center" py={12}>
              <Text fontSize="2xl" mb={2}>BarChart</Text>
              <Text fontSize="md" color="gray.400" fontWeight="semibold">
                No holdings yet
              </Text>
              <Text fontSize="sm" color="gray.600" mt={1}>
                Add your first stock to start tracking performance.
              </Text>
            </Box>
          ) : (
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th color="gray.500">Ticker</Th>
                  <Th color="gray.500" isNumeric>Shares</Th>
                  <Th color="gray.500" isNumeric>Cost Basis</Th>
                  <Th color="gray.500" isNumeric>Invested</Th>
                </Tr>
              </Thead>
              <Tbody>
                {holdings.map((holding) => {
                  const invested = holding.shares * holding.cost_basis;
                  return (
                    <Tr key={holding.ticker} _hover={{ bg: 'surface.cardHover' }} transition="background .15s ease">
                      <Td fontWeight="bold" color="white">{holding.ticker}</Td>
                      <Td isNumeric color="gray.300">{holding.shares}</Td>
                      <Td isNumeric color="gray.300">${holding.cost_basis.toFixed(2)}</Td>
                      <Td isNumeric color="blue.200" fontWeight="semibold">${invested.toFixed(2)}</Td>
                    </Tr>
                  );
                })}
              </Tbody>
            </Table>
          )}
        </Box>
      </Stack>
    </Box>
  );
};

export default PortfolioPage;