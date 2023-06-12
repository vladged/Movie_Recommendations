## Generate a marketing product description from a product fact sheet
class Prompt:

    def __init__(self,Favorite_Movies=None):
        if(Favorite_Movies is None):
            Favorite_Movies = "A Few Good Man;Stand by Me;Point Break;Pulp Fiction "
        self.Favorite_Movies = Favorite_Movies       

        self.prompt1 = f"Your task is to find movies which user would like based on the list \
        of the movies user likes. \
        Don't take genre into account, the most important factors are director, producer and cast. Explain your decision.\
        Produce a list of movies or shows with descriptions.\
        Also produce the URLs to Imdb for each show.\
        Please make each URL clickable, put it inside <a> HTML tag.\
        List of movies user likes: {self.Favorite_Movies}"
        
        #Use the list of movies and shows separated by semicolons and delimited with triple backticks.\
                
        
        self.prompt2 = f"Your task is to find movies and shows which user would like based on the list of the movies user likes. \
        Your decision should be based on critics' opinions from sites like Rotten Tomatoes and RogerEbert.\
        Explain your decision.\
        Don't take genre into account.\
        Produce a list of movies or shows with descriptions. \
        Also produce the URLs to IMDb for each show. \
        Please make each URL clickable, put it inside <a> HTML tag. \
        List of movies user likes: {self.Favorite_Movies}"
        
#         self.prompt3 = f"""
#         Your task is to find movies and shows which user would like based on the list of the movies and shows user likes. 
# Your decision should be based on critics opinion from the sites like Rotten Tomatoes.
# If a critics like the movies or shows from the list, you should assume that the user would like other movies or shows the critic like.
# Don't take genre into account.
# Use the list of movies and shows separated by semicolons and delimited with triple backticks.
# Produce a list of 10 movies or shows.
# The list of movies or shows user likes: ```{self.Favorite_Movies}```
#        """
        ## Issue 2. Text focuses on the wrong details
        #- Ask it to focus on the aspects that are relevant to the intended audience.

   