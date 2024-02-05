# Combining rules and machine learning

Currently, I am developing [Wordsmyth](https://github.com/ajskateboarder/wordsmyth), a star rating prediction model designed to tackle the bias and incorrectness of the consumer star system through sentiment analysis and rules. This system allows you to use the pros of both rule-based systems:

- simple to build and interpret
- less computationally expensive
- more predictability and accuracy in its domain

and machine learning:

- higher overall accuracy
- very dynamic
- easy to adapt to situations

With my project, I use the output of pre-trained sentiment analysis networks as inputs to a rule-based process to correct the outputs and quantify the sentiment information as a star rating.

![Wordsmyth flow](./rules-and-ml.png)

In simpler terms, this is the layout of the system:

![Alt text](./simple-layout.png)

What's honestly weird about this approach is that, in this ever-growing ecosystem of machine learning, there are so few applications of this approach online!!

# See

- https://kislayverma.com/programming/combining-rule-systems-and-machine-learning/
- https://nlathia.github.io/2020/10/ML-and-rule-engines.html
- https://github.com/koaning/human-learn
