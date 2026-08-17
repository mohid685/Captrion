import { Box, Flex, Text } from '@chakra-ui/react';

const Footer = () => (
  <Box className="app-footer" mt="auto" zIndex={1}>
    <Flex maxW="container.xl" mx="auto" px={{ base: 5, md: 6 }} py={5} align="center" justify="space-between" gap={4}>
      <Text color="white" fontWeight="700" fontSize="sm">Captrion</Text>
      <Text color="gray.500" fontSize="xs">© {new Date().getFullYear()} Captrion</Text>
    </Flex>
  </Box>
);

export default Footer;
