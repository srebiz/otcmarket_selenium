package com.otc.selenium;

import org.testng.annotations.BeforeTest;
import org.testng.annotations.Test;

public class OTCTestCase001 extends ScriptBase{
	
	
	@BeforeTest
	public void setURL(){
		
		super.setURL("http://www.otcmarkets.com/stock/CSTI/quote");
	}
	
	@Test
	public void TestCase001_1(){
		
		
		otcApp.verifyQuoteHeader("CSTI");
	

	}

	@Test
	public void TestCase001_2(){
		
		
       otcApp.verifyOpenWithinYearRange();
		

	}
}
