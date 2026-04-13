require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config({ path: "../.env" });

const INFURA_PROJECT_ID = process.env.INFURA_PROJECT_ID;
const PRIVATE_KEY       = process.env.PRIVATE_KEY;

if (!INFURA_PROJECT_ID) {
  throw new Error("INFURA_PROJECT_ID is not set — copy .env.example to .env.");
}

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.20",
  networks: {
    sepolia: {
      url: `https://sepolia.infura.io/v3/${INFURA_PROJECT_ID}`,
      accounts: PRIVATE_KEY ? [PRIVATE_KEY] : [],
    },
  },
};
