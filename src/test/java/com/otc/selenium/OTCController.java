package com.otc.selenium;

import org.apache.http.util.Asserts;
import org.openqa.selenium.WebDriver;
import org.testng.Assert;

public class OTCController {
	private WebDriver driver;
	private OTCModel  otcModel;
	
	public OTCController(WebDriver driver){
		this.driver = driver;
		otcModel = new OTCModel(driver);
	}
	
	
	public void verifyQuoteHeader(String quoteHeaderText){
		
		String symbolHeader = otcModel.symbol_QH_QX.getText();
		System.out.println(symbolHeader);
		Assert.assertEquals(quoteHeaderText,symbolHeader );
	}
	
	public void verifyOpenWithinYearRange(){
		
		String[] str = getYRange();
		double bottomPrice = Double.parseDouble(str[0]);
		double topPrice = Double.parseDouble(str[1]);
		int openPrice = 12; //Integer.parseInt(otcModel.open().getText());
		Assert.assertEquals(true,openPrice >= bottomPrice,"Open Price not lower then 52W Price Range");
		Assert.assertEquals(true,openPrice <= topPrice,"Open price not higer then 52W Price Range");
	}
    
	public String[] getYRange()
	{
		String[] range;
		
		range = otcModel.YearRange().getText().split("-");
		
		return range;
	}
}
