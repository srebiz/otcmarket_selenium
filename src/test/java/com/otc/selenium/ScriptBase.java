package com.otc.selenium;




import java.util.concurrent.TimeUnit;



import org.openqa.selenium.WebDriver;
import org.openqa.selenium.firefox.FirefoxBinary;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Optional;
import org.testng.annotations.Parameters;

public class ScriptBase {
	
	private WebDriver driver;
	public OTCController otcApp;
	private String url;  //"http://www.otcmarkets.com/stock/OTCM/quote"
	
	
	public void setURL(String url){
		this.url = url;
	}
	
	
	@Parameters({"browser,url"})
	@BeforeMethod
	public void setup(@Optional("rd_ff") String browser) throws Exception{
		
		if ( browser.contains("rd_ff")){
			driver = new FirefoxDriver();
		}
		
		otcApp = new OTCController(driver);

		 /*
1.        Using Selenium, write automation code to test the top portion 
		  (see screenshot below) of http://www.otcmarkets.com/stock/OTCM/quote. 
		  The candidate can come up with his own domain/range for each data point below.
		   The project should be published in a public project at Github.com.
2.        Using any available tool, create automation code to load test
 		  http://www.otcmarkets.com/marketplaces/otcqx with 10, 50, and 100 users concurrently. 
 		  We are interested to know what kind of tests will be made and what could be the expected results. 
 		  Again, please publish the code in a public project in Github.com.
		*/
		
		// Open AUT
		driver.navigate().to(url);
		
		// Set timeouts
		driver.manage().timeouts().implicitlyWait(60, TimeUnit.SECONDS);
		driver.manage().deleteAllCookies();
		driver.manage().window().maximize();
		
	}
	
	@AfterMethod
	public void tearDown(){
		
		
		driver.close();
		driver.quit();
		otcApp = null;
	}
	

}
