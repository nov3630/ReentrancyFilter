// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.4.19;

contract case0 {
    mapping(address => uint) public balances;
    function withdraw() public {
        uint bal = balances[msg.sender];
        require(bal > 0);

        msg.sender.call.value(1 ether)();

        balances[msg.sender] = 0;
    }
}
