## Generate a marketing product description from a product fact sheet
class Prompt:

    def __init__(self,Favorite_Movies=None):
        if(Favorite_Movies is None):
            Favorite_Movies = "A Few Good Man;Stand by Me;Point Break;Pulp Fiction "
        self.Favorite_Movies = Favorite_Movies       

        self.prompt1 = f"Your task is to find movies which user would like based on the list \
        of the movies user likes. \
        Don't take genre into account, the most important factors are director, producer and cast.\
        Use the list of movies separated by semicolons and delimited with triple backticks.\
        Produce a list of 10 movies with descriptions.\
        list of movies user likes: {self.Favorite_Movies}"
        
        self.prompt2= f"Your task is to find movies which user would like based on the list of the movies user likes.\
        \n\nYour decision should be based on critics' opinions from sites like Rotten Tomatoes.\n\nList of movies user \
        likes: {Favorite_Movies}\n\nProduce a list of 10 movies with descriptions.\n\n---\n"

        self.prompt3 = f"""
        Your task is to find movies which user would like based on the list of the movies user likes. 
Your decision should be based on critics opinion from the sites like Rotten Tomatoes.
If a critics like the movies from the list, you should assume that the user would like other movies the critic like.
Don't take genre into account.
Use the list of movies separated by semicolons and delimited with triple backticks.
Produce a list of 10 movies .
The list of movies user likes: ```{self.Favorite_Movies}```
       """
        ## Issue 2. Text focuses on the wrong details
        #- Ask it to focus on the aspects that are relevant to the intended audience.

   