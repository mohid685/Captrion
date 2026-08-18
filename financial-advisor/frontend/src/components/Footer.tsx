import { Box, Flex, HStack, Text } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Footer = () => {
  const { currentUser } = useAuth();

  return (
    <Box className="app-footer" mt="auto" zIndex={1}>
      <Flex
        maxW="container.xl"
        mx="auto"
        px={{ base: 5, md: 6 }}
        py={5}
        align="center"
        justify="space-between"
        flexWrap="wrap"
        gap={4}
      >
        <HStack spacing={4}>
          <Text color="white" fontWeight="700" fontSize="sm">
            Captrion
          </Text>
          {/* <Box display={{ base: 'none', sm: 'flex' }} className="footer-status">
            <span />
            All systems operational
          </Box> */}
        </HStack>

        <HStack spacing={{ base: 4, md: 6 }} fontSize="xs" color="gray.500">
          {currentUser ? (
            <>
              <Text as={RouterLink} to="/dashboard" _hover={{ color: 'blue.200' }} transition="color .15s ease">
                Dashboard
              </Text>
              <Text as={RouterLink} to="/chat" _hover={{ color: 'blue.200' }} transition="color .15s ease">
                Chat
              </Text>
              <Text as={RouterLink} to="/portfolio" _hover={{ color: 'blue.200' }} transition="color .15s ease">
                Portfolio
              </Text>
            </>
          ) : (
            <>
              <Text as={RouterLink} to="/login" _hover={{ color: 'blue.200' }} transition="color .15s ease">
                Login
              </Text>
              <Text as={RouterLink} to="/register" _hover={{ color: 'blue.200' }} transition="color .15s ease">
                Register
              </Text>
            </>
          )}
          <Text color="gray.600">© {new Date().getFullYear()} Captrion</Text>
        </HStack>
      </Flex>
    </Box>
  );
};

export default Footer;