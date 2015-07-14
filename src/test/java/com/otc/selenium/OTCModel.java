package com.otc.selenium;

import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.How;
import org.openqa.selenium.support.PageFactory;

public class OTCModel {
	
	private WebDriver driver;
	
	    
	@FindBy(how=How.XPATH,using=".//*[@id='xcompanyHeader']/div[1]/div[1]/div[1]/h3")
	public WebElement symbol_QH_QX;
	
	@FindBy(how=How.XPATH,using=".//*[@id='xcompanyInfo']/h3")
	public WebElement xCompanyInfo;
	
	@FindBy(how=How.XPATH,using=".//*[@id='xcompanyHeader']/div[1]/div[2]/div[1]/img")
	public WebElement companyLogo;
	
	@FindBy(how=How.XPATH,using=".//*[@id='xcompanyHeader']/div[4]")
	public WebElement companyInfo;
	
	@FindBy(how=How.XPATH,using=".//*[@id='priceChgBBO']/div/div[1]/span[1]")
	public WebElement lastPriceChange_price;
	
	@FindBy(how=How.XPATH,using=".//*[@id='tradeSummary']/div[1]/span[1]")
	public WebElement previousClose;
	
	@FindBy(how=How.XPATH,using="@id='tradeSummary']/div[2]/span[1]")
	public WebElement dailyRange;	
	
	@FindBy(how=How.XPATH,using=".//*[@id='tradeSummary']/div[1]/span[2]")
	public WebElement open;	
	
	@FindBy(how=How.XPATH,using=".//*[@id='tradeSummary']/div[2]/span[2]")
	public WebElement YearRange;
	
	@FindBy(how=How.XPATH,using=".//*[@id='tradeSummary']/div[3]/span[1]")
	public WebElement volume;
	
	@FindBy(how=How.XPATH,using=".//*[@id='tradeSummary']/div[3]/span[2]/span")
	public WebElement divident;
	
	
	public OTCModel(WebDriver driver){
		this.driver = driver;
		PageFactory.initElements(driver, this);
	}
	
	protected void highlightElement(WebElement element) {
		for (int i = 0; i < 2; i++) {
			JavascriptExecutor js = (JavascriptExecutor) driver;
			js.executeScript(
					"arguments[0].setAttribute('style', arguments[1]);",
					element, "color: green; border: 5px solid blue;");
			js.executeScript(
					"arguments[0].setAttribute('style', arguments[1]);",
					element, "");
		}
	}	
	
	//
	protected WebElement symbol_QH_QX(){
		highlightElement(symbol_QH_QX);
		return symbol_QH_QX;
	}
	
	
	//
	protected WebElement xCompanyInfo(){
		highlightElement(xCompanyInfo);
		return xCompanyInfo;
	}
	
	//
	protected WebElement companyLogo(){
		highlightElement(companyLogo);
		return companyLogo;
	}
	
	//
	protected WebElement companyInfo(){
		highlightElement(companyInfo);
		return companyInfo;
	}
	
	//
	protected WebElement lastPriceChange_price(){
		highlightElement(lastPriceChange_price);
		return lastPriceChange_price;
	}
	
	//
	protected WebElement previousClose(){
		highlightElement(previousClose);
		return previousClose;
	}
	
	//
	protected WebElement dailyRange(){
		highlightElement(dailyRange);
		return dailyRange;
	}
	
	//
	protected WebElement open(){
		highlightElement(open);
		return open;
	}
	
	//
	protected WebElement YearRange(){
		highlightElement(YearRange);
		return YearRange;
	}
	
	//
	protected WebElement volume(){
		highlightElement(volume);
		return volume;
	}
	
	//
	protected WebElement divident(){
		highlightElement(divident);
		return divident;
	}
	
}
