const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);

  const RewardToken = await hre.ethers.getContractFactory("RewardToken");
  const token = await RewardToken.deploy(deployer.address);
  await token.waitForDeployment();

  console.log("RewardToken deployed to:", await token.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
